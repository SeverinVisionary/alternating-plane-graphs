#!/bin/sh
# Exact serial command transcript; executed from repository root.
python3 -m pip install z3-solver==5.1.0.0
python3 exact_map_bool_sat.py --known-certificate certificates/known/order20.json --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py certificates/known/order20.json --expect-order 20
python3 verify_darts.py certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat"' "$LOG_DIR/bool_known_order20.json"
python3 exact_map_bool_sat.py --known-block results/blocks/A21.json --canonicalize-known-block --require-t0 --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_A21_socket_normal_form.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and .canonical == true and .control == "published-strict-block-canonicalized"' "$LOG_DIR/bool_known_A21_socket_normal_form.json"
python3 exact_map_postprocess.py "$LOG_DIR/bool_known_A21_socket_normal_form.json" --expected-order 21 --expected-block-t 0 --output "$LOG_DIR/bool_known_A21_socket_normal_form_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .closure_count == 9 and .r_gate.passed and .block_t_gate.passed and ([.closures[].passed] | all)' "$LOG_DIR/bool_known_A21_socket_normal_form_postprocess.json"
run_target 28 12
run_target 29 12
run_target 31 12
