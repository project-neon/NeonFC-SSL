# NeonFC-SSL (DRL Path) — Agent Reference

Only the DRL-relevant parts. Full project does more; this covers: **DRLCoach**, **Decision Layer (behavior tree)**, **EventSocket**, **Transformation Architecture**.

---

## DRLCoach (`coach/drl_coach.py`)

| Aspect | Detail |
|--------|--------|
| **Checkpoint source** | `shared/models/` (symlink from RL-Engine) |
| **Load on startup** | Yes — loads latest `.pt` for each role |
| **Hot-reload** | On `ModelUpdate` from Lynch (`:10002`) — replaces policy weights in-place |
| **Inference frequency** | 60 Hz (control loop) |
| **Transition output** | TCP `:10001` → Lynch, JSON lines: `{"cur_state":[16], "next_state":[16], "actions":{"goalkeeper":[4],"striker":[4]}}` |
| **State vector (16)** | Built in DRLCoach: `[gk_x, gk_y, gk_θ, gk_vx, gk_vy, gk_ω, st_x, st_y, st_θ, st_vx, st_vy, st_ω, ball_x, ball_y, ball_vx, ball_vy]` (NeonFC field-corner frame) |

---

## Transformation Architecture (Registry Pattern)

Decouples **model I/O** from **domain data** (MatchData, RobotRubric).

| Component | Role |
|-----------|------|
| `TransformationRegistry` | Auto-discovers `@register("name")` functions in `transformations/` |
| `PreProcess` | Binds models → input transformations; runs each once per tick; applies output transformation |
| Input transformation | `MatchData` → `torch.Tensor` (e.g., `"n_robots"` extracts 6D features per robot + ball) |
| Output transformation | `{model: action_tensor}` → `dict[RobotRubric]` (e.g., `"one_v_one_output"` maps to GK/Striker) |
| Persistence transformation | Optional — saves intermediate state for next-state in transition stream |

**Config** (in `neonfc.toml` under `coach.drl`):
```toml
persistence_transformation = "one_v_one"      # optional
output_transformation = "one_v_one_output"    # required
# per-model:
models = [
  {id = "striker", file_path = "...", transformation = "one_v_one", epsilon = 0.1},
  {id = "goalkeeper", file_path = "...", transformation = "one_v_one", epsilon = 0.0}
]
```

**Flow per tick:**
```
MatchData → PreProcess.process()
  → runs input transforms → {model_id: tensor}
  → Model.inference(tensor) → {model_id: action_tensor}
  → apply_output_transformation() → {robot_id: RobotRubric}
  → inject into behavior tree strategies
```

> **Key design:** Works with **N robots on the same team**. NeonFC only controls one team (Blue). For adversarial training, Lynch re-frames same-team robots as opponents (e.g., Blue striker ↔ Blue goalkeeper as adversaries). The transformation `n_robots` extracts features for any robot IDs — Lynch decides which IDs are "teammates" vs "opponents" in the state vector.

---

## Decision Layer — Behavior Tree

```
DecisionLayer (root)
├── RefereeMandatedBehaviors (highest priority)
├── FallbackSkills (go-to, kick, etc.)
└── DRLCoach (DRL leaf — active only when: play state + no referee override + DRL enabled)
```

| Point | Detail |
|-------|--------|
| **DRLCoach position** | Leaf under root; gated by `MasterState.play` + no referee override |
| **Override logic** | Referee → Fallback → DRL (DRL only runs when explicitly allowed) |
| **Add new DRL behavior** | Implement skill class in `layers/decision/skills/`, register in behavior tree config |
| **Key files** | `layers/decision/behavior_tree.py`, `layers/decision/skills/drl_skill.py` |

---

## EventSocket (`:10002` — TCP from Lynch)

| Message | Handler | Effect |
|---------|---------|--------|
| `ModelUpdate` | `DRLCoach.model_update()` | Hot-reloads policy weights from `file_path` |
| `MasterState` {play: bool} | `DecisionLayer.set_play_state()` | Gates DRLCoach activation |
| `EpsilonGreedy` | `DRLCoach.epsilon_greedy()` | Updates per-model exploration `epsilon` |

**EpsilonGreedy payload:**
```json
{
  "models": [
    {"id": "striker", "epsilon": 0.1},
    {"id": "goalkeeper", "epsilon": 0.0}
  ]
}
```
- Handler: `@event_callback(EventType.EPSILON_GREEDY)` in `drl_trainer.py`
- Effect: `model.epsilon = new_value` — used in `Model.inference()` for exploration:
  ```python
  if self.epsilon > 0 and random() < self.epsilon:
      action = add_noise(action)  # exploration
  ```

**Protocol:** JSON lines, one message per line.

---

## DRL-Relevant `neonfc.toml` Keys

| Key | Purpose |
|-----|---------|
| `event_socket.port` | Must be `10002` (matches Lynch) |
| `coach.drl.enabled` | Enable/disable DRLCoach in behavior tree |
| `coach.drl.checkpoint_path` | `shared/models/` (via symlink) |
| `coach.drl.roles` | `["striker", "goalkeeper"]` — must match RL-Engine `role_ids` |
| `team.color` | `blue` (DRL controls Blue 0=GK, 1=Striker) |

---

## DRL Debug Steps

| Symptom | First Checks |
|---------|--------------|
| DRLCoach not loading checkpoint | `shared/models/` exists? `.pt` files present? `neonfc.toml` `checkpoint_path` correct? |
| Transitions not reaching Lynch (`:10001`) | Lynch running? `:10001` open? Check `logs/NeonFC-SSL.log` for connection errors |
| ModelUpdate not triggering reload | Lynch sending `ModelUpdate`? Check Lynch logs. DRLCoach `on_model_update` called? |
| DRL not controlling robots | `MasterState.play=true`? Referee not overriding? Behavior tree selecting DRL leaf? Check decision layer logs |

---

## Run Command

```bash
# From RL-Control root:
./run.sh NeonFC-SSL
# Or direct:
poetry run neonfc --profile ../configs/neonfc.toml
```

---

> **Note:** See `RL-Control/agents.md` for orchestration, ports, shared dirs. See `LyNCh/agents.md` for harness interface.