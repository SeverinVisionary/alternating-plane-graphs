# Exact operational commands are those in CLOUD_BOOL_CAP_MOTIF_JOB.md, executed serially.
# Managed-checkout substitution: authoritative checkout HEAD/tree verified directly; no bundle used.
python3 -m pip install z3-solver
python3 exact_map_bool_sat.py --known-certificate certificates/known/order20.json --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py certificates/known/order20.json --expect-order 20
python3 verify_darts.py certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat"' "$LOG_DIR/bool_known_order20.json"
python3 exact_map_bool_sat.py --known-cap-block results/blocks/A21.json --require-t0 --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_A21_cap_motif.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and .lane == "closed" and .canonical == true and .require_cap_fans == true and .require_cap_interface == true and .require_cap_facets == true and .require_t0 == true and .control == "published-strict-block-capped-cap-normalized"' "$LOG_DIR/bool_known_A21_cap_motif.json"
python3 exact_map_postprocess.py "$LOG_DIR/bool_known_A21_cap_motif.json" --expected-order 21 --expected-block-t 0 --output "$LOG_DIR/bool_known_A21_cap_motif_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .cap_opening.passed and .closure_count == 9 and .block_t_gate.passed and .r_gate.passed and ([.closures[].passed] | all)' "$LOG_DIR/bool_known_A21_cap_motif_postprocess.json"
run_target 28 12
run_target 29 12
run_target 31 12
# run_target implementation and arguments were copied verbatim from CLOUD_BOOL_CAP_MOTIF_JOB.md.
# Profiles ran synchronously in this order, with no retries: 28/12, 29/12, 31/12.
# No target postprocessor ran because all raw dispositions were INCOMPLETE/unknown.
# Promotion was not started because no target postprocessor was CERTIFIED.
