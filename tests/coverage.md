# Карта покрытия автотестами

Обновлено: 2026-09-17 (S-08 UC-008 язык UI; прогон полного набора не выполнялся). Полный набор — `/use-tests`.

| Тест | Файл | Требования | Слой | Состояние UI | Примечание |
| --- | --- | --- | --- | --- | --- |
| test_should_generate_valid_fleets_when_window_allows | `tests/test_should_generate_valid_fleets_when_window_allows.py` | FT-009…FT-013 | happy | — | Domain placement |
| test_should_raise_when_start_window_already_elapsed | `tests/test_should_generate_valid_fleets_when_window_allows.py` | FT-010, NFT-015 | negative | — | Deadline already past |
| test_should_create_session_when_slot_free | `tests/test_should_create_session_when_slot_free.py` | FT-001, FT-016, A0149 | happy | — | Use case + FakeStore |
| test_should_reject_when_three_sessions_active | `tests/test_should_create_session_when_slot_free.py` | FT-049 | negative | — | Soft limit before generate |
| test_should_return_201_with_player_fleet_when_post_sessions | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | UC-001, FT-001, FT-014, FT-016, A0156, FT-080, A0158, OpenAPI | happy | — | ASGI + FakeStore; `remainTtlSeconds` — остаток на момент ответа (1799…1800), не пример 1800 |
| test_should_hide_backend_occupancy_when_session_created | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | FT-015, NFT-009 | happy | — | API wire shape |
| test_should_return_400_when_create_session_has_body | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | UC-001 5.1, A0157 | negative | — | |
| test_should_return_409_when_session_limit_reached | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | FT-049, A0156 | edge | — | 4th POST |
| test_should_return_503_when_placement_window_expires | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | FT-010, NFT-015, A0156 | negative | — | Monkeypatch placement |
| test_should_return_500_when_persist_fails_after_generation | `tests/test_should_return_201_with_player_fleet_when_post_sessions.py` | UC-001 E1, A0081 | negative | — | |
| test_should_omit_backend_fleet_when_mapping_session_state | `tests/test_should_omit_backend_fleet_when_mapping_session_state.py` | FT-015, OpenAPI SessionState | happy | — | DTO mapper |
| test_should_mark_miss_and_pass_turn_when_empty_cell | `tests/test_should_resolve_player_shot_when_legal.py` | FT-018, FT-017 | happy | — | Domain shot |
| test_should_mark_hit_and_keep_turn_when_deck_survives | `tests/test_should_resolve_player_shot_when_legal.py` | FT-019 | happy | — | |
| test_should_mark_sunk_and_perimeter_miss_when_last_deck | `tests/test_should_resolve_player_shot_when_legal.py` | FT-020, FT-021, FT-072 | happy | — | |
| test_should_reject_when_cell_already_checked | `tests/test_should_resolve_player_shot_when_legal.py` | FT-044 | negative | — | |
| test_should_reject_when_not_player_turn | `tests/test_should_resolve_player_shot_when_legal.py` | FT-046 | negative | — | |
| test_should_set_game_over_when_last_ship_sunk | `tests/test_should_resolve_player_shot_when_legal.py` | FT-071, FT-025, FT-026, A0005 | happy | — | Domain: last deck `SUNK` + `GAME_OVER` |
| test_should_reject_when_coordinates_out_of_board | `tests/test_should_resolve_player_shot_when_legal.py` | FT-045 | negative | — | |
| test_should_reject_when_match_already_over | `tests/test_should_resolve_player_shot_when_legal.py` | FT-047 | negative | — | |
| test_should_reject_second_shot_when_turn_already_passed | `tests/test_should_resolve_player_shot_when_legal.py` | FT-051 | negative | — | After accepted MISS |
| test_should_shift_ttl_anchor_when_shot_accepted | `tests/test_should_resolve_player_shot_when_legal.py` | FT-005, A0158 | happy | — | |
| test_should_keep_ttl_anchor_when_shot_rejected | `tests/test_should_resolve_player_shot_when_legal.py` | FT-005, A0158 | negative | — | Rejected shot does not move TTL |
| test_should_accept_when_corner_cell_unchecked | `tests/test_should_resolve_player_shot_when_legal.py` | UC-002 5.6, FT-007, FT-063 | edge | — | Corner `00` |
| test_should_return_400_shot_wrong_channel_when_post_shots | `tests/test_should_return_shot_events_when_party_ws.py` | FT-055, A0089 | negative | — | REST reject |
| test_should_send_snapshot_then_shot_resolved_when_ws_miss | `tests/test_should_return_shot_events_when_party_ws.py` | UC-002, FT-017, OpenAPI WS | happy | — | FakeStore + WS |
| test_should_send_shot_resolved_when_ws_hit | `tests/test_should_return_shot_events_when_party_ws.py` | UC-002, FT-019, FT-023, FT-063, OpenAPI | happy | — | WS HIT keeps Player turn |
| test_should_send_shot_resolved_when_ws_sunk | `tests/test_should_return_shot_events_when_party_ws.py` | UC-002, FT-020, FT-021, FT-024 | happy | — | WS SUNK + perimeter; not last ship |
| test_should_send_error_when_ws_cell_already_checked | `tests/test_should_return_shot_events_when_party_ws.py` | FT-044 | negative | — | Repeat cell after HIT |
| test_should_send_invalid_payload_error_when_shot_coords_wrong_type | `tests/test_should_return_shot_events_when_party_ws.py` | FT-070 | negative | — | column as string |
| test_should_send_error_when_shot_not_your_turn | `tests/test_should_return_shot_events_when_party_ws.py` | FT-046 | negative | — | WS error frame |
| test_should_reject_ws_when_session_unknown | `tests/test_should_return_shot_events_when_party_ws.py` | FT-067, A0001 | negative | — | Handshake close |
| test_should_leave_session_unchanged_when_post_shots | `tests/test_should_return_shot_events_when_party_ws.py` | FT-055, A0001 | negative | — | REST no mutate |
| test_should_send_invalid_payload_error_when_shot_missing_coords | `tests/test_should_return_shot_events_when_party_ws.py` | FT-070 | negative | — | |
| test_should_reject_second_ws_when_party_already_connected | `tests/test_should_return_shot_events_when_party_ws.py` | FT-068 | negative | — | |
| test_should_send_snapshot_when_ws_reconnects_after_drop | `tests/test_should_resume_session_when_ws_reconnects.py` | UC-006, FT-002, FT-005, FT-054, FT-080 | happy | — | Resume snapshot; TTL not shifted |
| test_should_keep_slot_when_ws_disconnects | `tests/test_should_resume_session_when_ws_reconnects.py` | FT-074, A0008 | happy | — | Drop keeps slot |
| test_should_replace_ws_when_previous_socket_is_stale | `tests/test_should_resume_session_when_ws_reconnects.py` | A0133, FT-054 | happy | — | Half-open replace |
| test_should_reject_second_ws_when_party_already_connected | `tests/test_should_resume_session_when_ws_reconnects.py` | FT-068, A0002 | negative | — | Live second client; first keeps channel |
| test_should_send_ttl_expired_when_idle_elapses_while_connected | `tests/test_should_resume_session_when_ws_reconnects.py` | FT-066, FT-053, OpenAPI TtlExpiredEvent | negative | — | No GAME_OVER / ledger |
| test_should_send_equivalent_snapshot_when_ws_resumes_with_shots | `tests/test_should_resume_session_when_ws_reconnects.py` | UC-006, FT-002, FT-054, NFT-007, OpenAPI sessionSnapshot | happy | — | Boards + shots + turn after drop |
| test_should_reject_ws_when_session_id_malformed | `tests/test_should_resume_session_when_ws_reconnects.py` | FT-067, UC-006 5.1, A0001, OpenAPI 404 | negative | — | 32-char non-hex; close 1008 |
| test_should_accept_resume_when_ttl_nearly_elapsed | `tests/test_should_resume_session_when_ws_reconnects.py` | UC-006 5.6, FT-005, A0022 | edge | — | Remain seconds; ttl_anchor unchanged |
| test_should_reject_ws_when_reconnects_after_ttl_expired | `tests/test_should_resume_session_when_ws_reconnects.py` | FT-067, FT-066, FT-053, A0022 | negative | — | Handshake after ttlExpired; no ledger |
| test_should_send_game_over_and_delete_when_last_ship_sunk | `tests/test_should_return_shot_events_when_party_ws.py` | FT-071, A0005, A0145, FT-039, OpenAPI WS | happy | — | `shotResolved` SUNK then separate `gameOver`; one Record; JSON deleted |
| test_should_apply_player_shot_when_session_exists | `tests/test_should_apply_player_shot_when_session_exists.py` | FT-017 | happy | — | Use case |
| test_should_raise_when_session_missing_on_shot | `tests/test_should_apply_player_shot_when_session_exists.py` | UC-002 E1 | negative | — | |
| test_should_raise_persist_error_when_save_fails_after_shot | `tests/test_should_apply_player_shot_when_session_exists.py` | UC-002 E2 | negative | — | |
| test_should_post_sessions_without_body_when_creating | `tests/test_should_post_sessions_when_client_starts.py` | UC-001, OpenAPI, A0155 | happy | — | urllib mock, POST no body |
| test_should_return_success_when_http_201 | `tests/test_should_post_sessions_when_client_starts.py` | UC-001, FT-001, FT-014, FT-016, A0156 | happy | — | Client 201 → scene |
| test_should_return_limit_error_when_http_409 | `tests/test_should_post_sessions_when_client_starts.py` | FT-049, A0156, A0157 | negative | — | Client 409, not ASGI |
| test_should_return_timeout_when_network_times_out | `tests/test_should_post_sessions_when_client_starts.py` | UC-001 5.2, A0123 | negative | — | TimeoutError mock |
| test_should_mark_player_decks_when_mapping_session | `tests/test_should_post_sessions_when_client_starts.py` | FT-006, FT-014 | happy | — | Client SessionState → cells |
| test_should_hide_enemy_occupancy_when_mapping_backend_board | `tests/test_should_post_sessions_when_client_starts.py` | FT-015 | happy | — | Client ignores leaked occupancy; Computer fleet is FT-009 placeholders, not `[]` |
| test_should_fill_computer_fleet_when_session_starts | `tests/test_should_fill_computer_fleet_when_session_starts.py` | FT-009, FT-015 | happy | — | `placeholder_backend_fleet`: 10 INTACT, `hide_intact_bars` |
| test_should_map_ten_player_ships_when_fleet_payload_complete | `tests/test_should_fill_computer_fleet_when_session_starts.py` | FT-009 | happy | — | 10+10 after start payload; coords on player decks |
| test_should_show_loading_when_start_match_clicked | `tests/test_should_show_battle_when_start_succeeds.py` | UC-001 | happy | empty → loading | Оракул `isVisibleTo(lobby)`, не `isVisible()` (окно без `show()`); взаимное исключение empty/loading/error |
| test_should_show_slot_error_when_limit_reached | `tests/test_should_show_battle_when_start_succeeds.py` | FT-049, A0157 | negative | error | То же; лобби остаётся; 409 text; empty и loading скрыты |
| test_should_show_timeout_error_when_server_silent | `tests/test_should_show_battle_when_start_succeeds.py` | UC-001 5.2, A0123 | negative | error | То же; err_timeout; menu trigger; empty и loading скрыты |
| test_should_show_own_fleet_without_enemy_ships_when_start_succeeds | `tests/test_should_show_battle_when_start_succeeds.py` | UC-001, FT-014, FT-015, FT-016 | happy | success | Own decks; Computer board empty of ships; live Computer fleet = FT-009 INTACT, not `[]` |
| test_should_return_zero_snapshot_when_no_records | `tests/test_should_return_zeros_when_statistics_empty.py` | UC-007 5.6, FT-041 | happy | — | Domain empty ledger |
| test_should_average_shots_when_records_exist | `tests/test_should_return_zeros_when_statistics_empty.py` | FT-038…FT-041, A0088 | happy | — | Mean of Record.shots |
| test_should_reject_when_counter_wins_exceed_games | `tests/test_should_return_zeros_when_statistics_empty.py` | UC-007 E1 | negative | — | Invariant |
| test_should_reject_when_zero_games_have_nonzero_totals | `tests/test_should_return_zeros_when_statistics_empty.py` | UC-007 E1 | negative | — | HASH leftover vs games=0 |
| test_should_average_zero_when_surrender_has_no_shots | `tests/test_should_return_zeros_when_statistics_empty.py` | FT-041, A0105 | edge | — | Surrender shots=0 |
| test_should_return_zeros_when_get_statistics_empty | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007, OpenAPI getStatistics | happy | — | HTTP zeros |
| test_should_leave_session_untouched_when_get_statistics | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 шаг 4, A0121 | happy | — | No TTL / session mutate |
| test_should_return_aggregates_when_ledger_has_records | `tests/test_should_return_aggregates_when_get_statistics.py` | FT-042, A0159 | happy | — | Fake records, not production stub |
| test_should_return_500_when_ledger_inconsistent | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 E1 | negative | — | 500 INTERNAL_ERROR |
| test_should_read_hash_counters_when_records_empty | `tests/test_should_return_aggregates_when_get_statistics.py` | S-05 HASH read model | happy | — | Use case + counters |
| test_should_raise_ledger_read_when_store_fails | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 E1 | negative | — | Use case |
| test_should_return_500_when_ledger_unavailable | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 E1, OpenAPI 500 | negative | — | HTTP store fail |
| test_should_return_hash_snapshot_when_records_empty | `tests/test_should_return_aggregates_when_get_statistics.py` | FT-042, A0159, OpenAPI populated | happy | — | HTTP HASH, avgShots 47.3 |
| test_should_leave_ledger_untouched_when_get_statistics | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 E2, FT-056 | happy | — | GET does not mutate ledger |
| test_should_reject_when_post_statistics | `tests/test_should_return_aggregates_when_get_statistics.py` | UC-007 5.1 / E2 | negative | — | 405 on write |
| test_should_read_hash_when_records_list_empty | `tests/test_should_read_ledger_when_redis_keys_present.py` | FT-038…FT-041, A0159 | happy | — | RedisLedgerStore HASH mock |
| test_should_prefer_list_records_when_hash_differs | `tests/test_should_read_ledger_when_redis_keys_present.py` | A0088 | edge | — | LIST wins over HASH |
| test_should_raise_inconsistent_when_record_json_corrupt | `tests/test_should_read_ledger_when_redis_keys_present.py` | UC-007 E1 | negative | — | Corrupt LIST JSON |
| test_should_raise_ledger_read_when_redis_errors | `tests/test_should_read_ledger_when_redis_keys_present.py` | UC-007 E1 | negative | — | RedisError → LedgerReadError |
| test_should_get_statistics_without_body_when_requesting | `tests/test_should_get_statistics_when_client_requests.py` | UC-007, OpenAPI getStatistics, FT-042 | happy | — | urllib mock, GET no body |
| test_should_return_success_when_http_200_populated | `tests/test_should_get_statistics_when_client_requests.py` | US-007 AC2, FT-038…FT-042, A0159 | happy | — | Client 200 → Snapshot |
| test_should_return_zero_snapshot_when_http_200_empty | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 5.6, US-007 AC4, FT-041 | happy | — | games==0 success, not error |
| test_should_return_http_error_when_status_500 | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 E1 | negative | — | Client 500 INTERNAL_ERROR |
| test_should_return_timeout_when_statistics_times_out | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 5.2 | negative | — | TimeoutError mock |
| test_should_return_unreachable_when_url_fails | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 5.2 | negative | — | URLError → unreachable |
| test_should_treat_inconsistent_payload_as_internal_error | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 E1 | negative | — | 200 wins ≠ games |
| test_should_show_http_status_when_statistics_missing | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 | negative | — | FastAPI 404 `detail`, not INTERNAL_ERROR |
| test_should_reject_when_zero_games_have_nonzero_avg | `tests/test_should_get_statistics_when_client_requests.py` | UC-007 5.6, FT-041 | edge | — | snapshot_from_payload |
| test_should_format_avg_shots_with_one_decimal | `tests/test_should_get_statistics_when_client_requests.py` | A0159 | edge | — | Display `0.0` / `47.3` |
| test_should_skip_statistics_fetch_when_window_constructed | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | S-01, UC-007 | edge | — | Constructor: no GET; `self.lobby` / start-match intact |
| test_should_show_stats_loading_when_first_shown | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 | happy | loading | showEvent; KPI hidden; `lobby-stats-loading` |
| test_should_show_empty_zeros_when_games_are_zero | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 5.6, US-007 AC4 | happy | empty | empty ≠ error; kpi-games=0 |
| test_should_show_kpi_values_when_statistics_succeed | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | US-007 AC1–AC2, FT-038…FT-042 | happy | success | lobby KPI from snapshot |
| test_should_show_stats_error_when_server_silent | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 5.2 | negative | error | err_timeout; start-match still enabled |
| test_should_show_stats_error_when_http_fails | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 E1 | negative | error | HTTP text; empty banner hidden |
| test_should_request_statistics_when_returning_to_lobby | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007, A0135 | happy | loading | `_show_lobby` while visible |
| test_should_request_statistics_when_stats_dialog_opens | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 | happy | loading / dialog | `open-stats` / `menu-stats`; `exec` patched |
| test_should_request_statistics_when_refresh_clicked | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007, A0135 | happy | loading / dialog | `stats-refresh` |
| test_should_show_dialog_empty_when_games_are_zero | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 5.6 | happy | empty / dialog | `stats-empty`; dialog KPI zeros |
| test_should_show_dialog_success_when_snapshot_populated | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | US-007 AC2 | happy | success / dialog | dialog-kpi-* |
| test_should_ignore_second_request_when_stats_already_loading | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | UC-007 | edge | loading | No second worker.start |
| test_should_emit_outcome_when_statistics_worker_runs | `tests/test_should_show_lobby_kpis_when_statistics_succeed.py` | FT-042 | happy | — | `run()` + mock get_statistics |
| test_should_build_party_ws_url_when_http_base | `tests/test_should_send_ws_shot_when_client_aims.py` | FT-055, OpenAPI WS | happy | — | `party_ws_url` → `/sessions/{id}/ws` |
| test_should_use_wss_when_https_base | `tests/test_should_send_ws_shot_when_client_aims.py` | FT-055 | edge | — | https → wss |
| test_should_emit_shot_json_when_send_shot | `tests/test_should_send_ws_shot_when_client_aims.py` | UC-002, FT-017, FT-055 | happy | — | JSON `type=shot`; поток не стартует |
| test_should_mark_miss_and_pass_turn_when_shot_resolved | `tests/test_should_send_ws_shot_when_client_aims.py` | FT-018, FT-017 | happy | — | `apply_shot_resolved` |
| test_should_mark_hit_and_keep_turn_when_shot_resolved | `tests/test_should_send_ws_shot_when_client_aims.py` | FT-019, FT-023 | happy | — | |
| test_should_mark_sunk_and_perimeter_when_shot_resolved | `tests/test_should_send_ws_shot_when_client_aims.py` | FT-020, FT-021, FT-024 | happy | — | |
| test_should_ignore_frame_when_seq_stale | `tests/test_should_send_ws_shot_when_client_aims.py` | A0124, OpenAPI seq | edge | — | |
| test_should_show_channel_loading_when_battle_opens | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | UC-002 | happy | loading | `battle-channel-loading`; `computer-board` |
| test_should_show_shot_empty_when_snapshot_has_no_shots | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | UC-002 | happy | empty | empty ≠ error; `battle-shot-empty` |
| test_should_send_ws_shot_when_computer_board_clicked | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-017, FT-055 | happy | loading | Клик `computer-board` → WS, не REST |
| test_should_show_shot_loading_when_cell_clicked | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | A0116, UC-002 | happy | loading | `battle-shot-loading` |
| test_should_ignore_second_click_when_shot_pending | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | A0116 | edge | loading | |
| test_should_not_send_shot_when_channel_still_loading | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | UC-002 | edge | loading | Клик до snapshot |
| test_should_not_send_shot_when_player_board_clicked | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-048 | negative | empty | `player-board` |
| test_should_show_miss_when_shot_resolved_arrives | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-018 | happy | success | Кадр сервера, не ход Компьютера |
| test_should_show_hit_when_shot_resolved_arrives | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-019 | happy | success | |
| test_should_show_sunk_when_shot_resolved_arrives | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-020, FT-021 | happy | success | |
| test_should_show_shot_error_when_cell_already_checked | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | FT-044 | negative | error | `battle-shot-error`; NFT-019 клетка |
| test_should_show_channel_error_when_handshake_times_out | `tests/test_should_show_shot_result_when_computer_board_clicked.py` | UC-002 5.2 | negative | error | `battle-channel-error`; empty скрыт |
| test_should_pick_max_weight_cell_when_hunt_mode | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-030, FT-064 | happy | — | Hunt density |
| test_should_zero_cells_outside_cross_when_one_hit | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-031, FT-032, FT-058 | happy | — | Target cross |
| test_should_restrict_axis_when_two_hits_on_line | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-058 | happy | — | Target axis |
| test_should_include_gap_on_axis_when_two_hits_skip_decks | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-058, A0026 | edge | — | UNCHECKED between HIT |
| test_should_include_cells_past_inner_hit_when_axis_has_gaps | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-058 | edge | — | HIT не обрывает span |
| test_should_finish_first_wounded_when_two_ships_hit | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-079 | happy | — | One wounded ship first |
| test_should_return_empty_aim_when_no_length_two_fit | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-065 | negative | — | Empty heatmap |
| test_should_not_use_hidden_decks_when_computing_hunt | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-050 | happy | — | Marks only |
| test_should_omit_sunk_lengths_when_listing_remaining | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-029 | happy | — | SUNK excluded, wounded kept |
| test_should_change_hunt_density_when_remaining_lengths_differ | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-028, FT-029 | happy | — | Hunt (1) vs (4) |
| test_should_assign_equal_max_inside_cross_when_target_mode | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-033 | happy | — | Cross leaders |
| test_should_pick_random_leader_when_hunt_weights_tie | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | FT-034 | edge | — | Random among max Hunt |
| test_should_return_empty_aim_when_turn_is_player | `tests/test_should_pick_heatmap_cell_when_backend_aims.py` | UC-003 | negative | — | Aim only on Backend turn |
| test_should_mark_miss_and_pass_turn_when_backend_misses | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-027 | happy | — | Domain backend MISS |
| test_should_keep_turn_when_backend_hits | `tests/test_should_resolve_backend_shot_when_legal.py` | UC-003 шаг 5 | happy | — | HIT keeps Backend |
| test_should_keep_turn_and_mark_perimeter_when_backend_sinks | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-021, UC-003 | happy | — | SUNK + buffer |
| test_should_set_game_over_when_backend_sinks_last_ship | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-025 | happy | — | Domain; ledger UC-004 later |
| test_should_reject_when_backend_shoots_on_player_turn | `tests/test_should_resolve_backend_shot_when_legal.py` | UC-003 5.4, FT-046 | negative | — | |
| test_should_reject_when_backend_cell_already_checked | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-044 | negative | — | Player board |
| test_should_reject_when_backend_shoots_after_game_over | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-047 | negative | — | |
| test_should_shift_ttl_anchor_when_backend_shot_accepted | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-005, A0158 | happy | — | |
| test_should_keep_ttl_anchor_when_backend_shot_rejected | `tests/test_should_resolve_backend_shot_when_legal.py` | FT-005, A0158 | negative | — | |
| test_should_apply_backend_shot_when_turn_is_backend | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-027 | happy | — | Use case |
| test_should_stop_chain_when_backend_misses | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | UC-003 | happy | — | Chain stops on MISS |
| test_should_continue_when_backend_hits | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | UC-003 5.1 | happy | — | HIT/SUNK chain |
| test_should_abort_when_heatmap_empty_and_fleet_alive | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-075, FT-076 | negative | — | No shot; delete is WS |
| test_should_raise_when_session_missing_on_backend_turn | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | UC-003 | negative | — | |
| test_should_set_game_over_without_shot_when_heatmap_empty_and_fleet_sunk | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-052, FT-065 | edge | — | Empty heatmap + fleet lost; no shot |
| test_should_recompute_aim_when_backend_continues_after_hit | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-028 | happy | — | Chain: second cell ≠ first |
| test_should_leave_peer_session_when_backend_plays | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-003, UC-003 5.5 | edge | — | Session B unchanged |
| test_should_raise_persist_error_when_save_fails_after_backend_shot | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | UC-003 E2 | negative | — | |
| test_should_shoot_unchecked_between_hits_when_battleship_has_gaps | `tests/test_should_play_backend_turns_when_heatmap_ready.py` | FT-058, FT-033, UC-003 5.1 | edge | — | Оракул: первый выстрел в UNCHECKED между HIT, не abort; серия до SUNK/GAME_OVER на одном линкоре не входит в эталон |
| test_should_send_session_aborted_when_heatmap_empty | `tests/test_should_return_shot_events_when_party_ws.py` | FT-076, FT-075, A0106, A0027 | negative | — | WS then delete; RU/EN; Ledger unchanged |
| test_should_send_backend_shot_when_battleship_hits_skip_decks | `tests/test_should_return_shot_events_when_party_ws.py` | FT-058, FT-033, UC-003 5.1 | edge | — | Оракул: первый кадр Backend = shotResolved в зазор оси, не abort; слот после GAME_OVER (FT-004) не читаем |
| test_should_send_backend_miss_when_player_misses | `tests/test_should_return_shot_events_when_party_ws.py` | FT-036, FT-027, FT-050, OpenAPI WS | happy | — | Deterministic Backend MISS frame |
| test_should_send_game_over_when_backend_sinks_last_player_ship | `tests/test_should_return_shot_events_when_party_ws.py` | FT-036, FT-025, FT-040, A0005 | happy | — | winner=Backend; SUNK then separate `gameOver`; one Record |
| test_should_reject_ws_when_session_aborted_already_deleted | `tests/test_should_return_shot_events_when_party_ws.py` | FT-067, FT-075 | negative | — | Handshake close after abort |
| test_should_reject_ws_when_game_over_already_deleted | `tests/test_should_return_shot_events_when_party_ws.py` | A0145, FT-067 | negative | — | Reconnect after `gameOver` = unknown id; Ledger stays 1 |
| test_should_send_game_over_when_heatmap_empty_and_fleet_sunk | `tests/test_should_return_shot_events_when_party_ws.py` | FT-052, FT-065, A0005, A0145 | edge | — | Player MISS then `gameOver` Backend; no Backend `shotResolved` |
| test_should_leave_ledger_when_idle_ttl_expired | `tests/test_should_return_shot_events_when_party_ws.py` | FT-053, A0027, UC-004 E2 | negative | — | Handshake refuse; no Record |
| test_should_leave_ledger_when_game_over_session_reconnects | `tests/test_should_return_shot_events_when_party_ws.py` | UC-004 5.1, A0145 | negative | — | Leftover `GameOver` JSON deleted; no Ledger append |
| test_should_append_ledger_and_release_slot_when_game_over | `tests/test_should_commit_ledger_when_game_over.py` | A0128, A0129, FT-038, FT-039 | happy | — | One Record; slot free; JSON still in store |
| test_should_not_double_count_when_commit_retried | `tests/test_should_commit_ledger_when_game_over.py` | A0129, FT-056 | edge | — | Second execute is no-op |
| test_should_retry_write_without_second_row_when_ledger_fails_once | `tests/test_should_commit_ledger_when_game_over.py` | UC-004 E1, A0129 | edge | — | One fail then success; one Record |
| test_should_raise_persist_when_ledger_write_exhausted | `tests/test_should_commit_ledger_when_game_over.py` | UC-004 E1 | negative | — | Three write fails; no Record |
| test_should_record_ledger_when_heatmap_empty_and_fleet_sunk | `tests/test_should_commit_ledger_when_game_over.py` | FT-052, FT-040, FT-065 | edge | — | Use case; no abort; Backend win |
| test_should_count_backend_win_when_commit_game_over | `tests/test_should_commit_ledger_when_game_over.py` | FT-040, UC-004 5.6 | happy | — | CommitGameOver Backend counters |
| test_should_set_avg_shots_when_first_game_commits | `tests/test_should_commit_ledger_when_game_over.py` | FT-041, UC-004 5.6 | edge | — | First Record; avg = that party's shots |
| test_should_reject_commit_when_status_is_active | `tests/test_should_commit_ledger_when_game_over.py` | A0027, FT-056 | negative | — | Active session cannot append Ledger |
| test_should_commit_ledger_when_player_sinks_last_ship | `tests/test_should_commit_ledger_when_game_over.py` | A0128, FT-071, FT-026 | happy | — | ApplyPlayerShot wires ledger; JSON remains |
| test_should_commit_ledger_when_backend_sinks_last_ship | `tests/test_should_commit_ledger_when_game_over.py` | FT-025, FT-040 | happy | — | PlayBackendTurns last deck, not empty heatmap |
| test_should_write_record_once_when_redis_commits | `tests/test_should_write_ledger_when_redis_commits.py` | A0088, A0129, FT-056 | happy | — | FakeRedis eval; second commit no-op |
| test_should_raise_ledger_write_when_redis_errors | `tests/test_should_write_ledger_when_redis_commits.py` | UC-004 E1 | negative | — | RedisError → LedgerWriteError |
| test_should_increment_backend_wins_when_redis_commits | `tests/test_should_write_ledger_when_redis_commits.py` | FT-040, A0129 | happy | — | HASH `backendWins` |
| test_should_mark_player_cell_when_backend_misses | `tests/test_should_apply_backend_shot_when_frame_arrives.py` | UC-003 шаг 7, FT-036 | happy | — | `apply_shot_resolved` shooter=Backend → player_cells |
| test_should_keep_backend_turn_when_backend_hits | `tests/test_should_apply_backend_shot_when_frame_arrives.py` | UC-003, FT-036 | happy | — | HIT keeps `player_turn=False`; Computer board Unchecked |
| test_should_mark_sunk_on_player_board_when_backend_sinks | `tests/test_should_apply_backend_shot_when_frame_arrives.py` | FT-036, FT-021 | happy | — | SUNK + perimeter on Player field |
| test_should_ignore_heatmap_when_backend_shot_resolved | `tests/test_should_apply_backend_shot_when_frame_arrives.py` | FT-050, A0095 | edge | — | heatmap/Hunt extra keys not stored on scene |
| test_should_show_player_mark_when_backend_shot_arrives | `tests/test_should_show_computer_shot_when_backend_aims.py` | UC-003 шаг 7, FT-036 | happy | success | `player-board` mark; Computer cell Unchecked |
| test_should_show_backend_toast_when_computer_aims | `tests/test_should_show_computer_shot_when_backend_aims.py` | FT-036 | happy | success | `toast_backend_shot`, не toast_hit игрока |
| test_should_show_computer_turn_when_backend_keeps_turn | `tests/test_should_show_computer_shot_when_backend_aims.py` | A0117, UC-003 шаг 7 | happy | success | `battle-computer-turn`; анимация без `exec` |
| test_should_hide_computer_turn_when_backend_misses | `tests/test_should_show_computer_shot_when_backend_aims.py` | FT-036 | happy | success | Aiming скрыт; клик по `computer-board` снова шлёт WS |
| test_should_pulse_player_board_when_backend_shot_arrives | `tests/test_should_show_computer_shot_when_backend_aims.py` | A0117 | happy | success | Пульс `player-board`, не `computer-board` |
| test_should_not_send_shot_when_not_player_turn | `tests/test_should_show_computer_shot_when_backend_aims.py` | FT-036 | negative | disabled | Клик режется `player_turn`; `err_not_turn` |
| test_should_omit_heatmap_when_backend_frame_arrives | `tests/test_should_show_computer_shot_when_backend_aims.py` | FT-050 | happy | success | Нет виджета heatmap; текст aiming, не Hunt/Target |
| test_should_wound_player_ship_when_backend_hits_deck | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-019, FT-036 | happy | — | `apply_shot_resolved` → player WOUNDED |
| test_should_sink_player_ship_when_backend_sinks | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-020, FT-036 | happy | — | Backend SUNK → all player decks |
| test_should_hide_computer_type_when_player_hits | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-015, FT-019 | happy | — | 9 INTACT named + 1 unnamed WOUNDED; `len==10`; не 10+1 |
| test_should_keep_ten_computer_ships_when_player_hits | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-009, FT-015, FT-019 | happy | — | Явный `len(backend_ships)==10` после первого HIT |
| test_should_reveal_computer_type_when_player_sinks | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-015, FT-020, FT-021 | happy | — | Один кадр: все палубы `SUNK` (1–4 клетки → катер…линкор); 1 SUNK + 9 INTACT = 10 |
| test_should_sink_computer_cruiser_when_hit_hit_sunk_chain | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-015, FT-019, FT-020, FT-021 | happy | — | HIT, HIT, SUNK: 1 крейсер SUNK, 0 unknown WOUNDED, 9 INTACT; `len==10` |
| test_should_keep_unknown_wounded_when_other_ship_hit_before_sunk | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-015, FT-019, FT-020 | edge | — | 1 SUNK + 1 unnamed WOUNDED + 8 INTACT = 10 |
| test_should_leave_fleets_when_player_misses | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-018 | edge | — | MISS не трогает ряды |
| test_should_leave_fleets_when_backend_misses | `tests/test_should_update_fleets_when_shot_resolved.py` | FT-036 | edge | — | MISS не трогает ряды |
| test_should_show_fleet_tab_when_battle_opens | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-009 | happy | success | `fleet_title`; `BattleScreen` без `exec` |
| test_should_show_fleet_headings_when_battle_opens | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-009 | happy | success | `fleet_player` / `fleet_backend`; `CardTitle` |
| test_should_show_ten_rows_per_side_when_battle_opens | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-009 | happy | success | 10+10 строк панели |
| test_should_hide_intact_enemy_decks_when_battle_opens | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-015 | happy | success | INTACT Computer: □, без ■ |
| test_should_show_player_type_and_intact_when_battle_opens | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-009 | happy | success | Игрок: тип + Цел |
| test_should_show_wounded_without_type_when_player_hits | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-015, FT-019 | happy | success | WOUNDED без имени типа; 10 строк панели, не 11 |
| test_should_show_computer_type_when_player_sinks | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-015, FT-020 | happy | success | SUNK 1 клетка → катер; 10 строк |
| test_should_show_player_wounded_when_backend_hits | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-019, FT-036 | happy | success | MainWindow кадр Backend → панель Игрока |
| test_should_show_computer_wounded_when_player_hit_arrives | `tests/test_should_show_fleet_composition_when_battle_opens.py` | FT-015, FT-019 | happy | success | MainWindow кадр Player HIT → панель Компьютера; 10 строк |
| test_should_set_match_over_when_game_over_arrives | `tests/test_should_apply_game_over_when_frame_arrives.py` | UC-004 шаг 5, A0118 | happy | — | `apply_game_over`; match_over; ход закрыт |
| test_should_mark_computer_win_when_backend_is_winner | `tests/test_should_apply_game_over_when_frame_arrives.py` | UC-004 | happy | — | winner=Backend → player_won False |
| test_should_mark_surrender_when_game_over_arrives | `tests/test_should_apply_game_over_when_frame_arrives.py` | UC-005, FT-077 | happy | — | `endReason=Surrender`; seq omitted; shot_count=0 |
| test_should_count_local_shots_when_seq_omitted | `tests/test_should_apply_game_over_when_frame_arrives.py` | OpenAPI GameOverEvent | edge | — | seq omitted → len(shots) |
| test_should_reject_when_game_over_fields_invalid | `tests/test_should_apply_game_over_when_frame_arrives.py` | UC-004 | negative | — | Невалидный winner; сцена не замирает |
| test_should_keep_sunk_marks_when_game_over_follows | `tests/test_should_apply_game_over_when_frame_arrives.py` | A0005, FT-071 | happy | — | SUNK отдельно; gameOver не перекрашивает клетки |
| test_should_fill_surrender_reason_when_dialog_presents | `tests/test_should_show_match_result_when_game_over.py` | UC-005, FT-077 | happy | dialog | `game-over-reason` = Сдача; не FleetLost |
| test_should_fill_result_labels_when_dialog_presents | `tests/test_should_show_match_result_when_game_over.py` | A0118 | happy | dialog | `game-over-*` селекторы; FleetLost, не сдача |
| test_should_show_result_dialog_when_game_over_arrives | `tests/test_should_show_match_result_when_game_over.py` | UC-004 шаг 5, A0118, A0005 | happy | dialog | SUNK затем `gameOver`; `exec` патч; лобби после |
| test_should_keep_sunk_on_board_when_game_over_follows | `tests/test_should_show_match_result_when_game_over.py` | A0005 | happy | success | `computer-board` клетка SUNK после кадра |
| test_should_not_send_shot_when_match_already_over | `tests/test_should_show_match_result_when_game_over.py` | FT-047, A0118 | negative | disabled | Клик `computer-board` не шлёт WS; сдача выкл. |
| test_should_show_lobby_when_game_over_closed | `tests/test_should_show_match_result_when_game_over.py` | A0118 | happy | dialog | `game-over-close` → лобби, без снимка партии |
| test_should_start_new_match_when_game_over_new_clicked | `tests/test_should_show_match_result_when_game_over.py` | A0118 | happy | dialog | `game-over-new-match` → CreateSessionWorker.start |
| test_should_open_stats_when_game_over_stats_clicked | `tests/test_should_show_match_result_when_game_over.py` | A0118 | happy | dialog | `game-over-open-stats`; stats `exec` патч |
| test_should_request_statistics_when_game_over_returns_to_lobby | `tests/test_should_show_match_result_when_game_over.py` | A0135, UC-004 шаг 5 | happy | loading | После GAME_OVER GET /statistics (воркер не HTTP) |
| test_should_ignore_second_game_over_when_result_already_shown | `tests/test_should_show_match_result_when_game_over.py` | A0118 | edge | dialog | Второй кадр не открывает диалог снова |
| test_should_mark_backend_win_when_surrender_applied | `tests/test_should_apply_surrender_when_session_active.py` | FT-077, FT-026 | happy | — | Domain apply_surrender |
| test_should_allow_surrender_when_backend_turn | `tests/test_should_apply_surrender_when_session_active.py` | A0092, A0100, FT-077 | happy | — | Domain; ход Backend |
| test_should_reject_surrender_when_match_already_over | `tests/test_should_apply_surrender_when_session_active.py` | FT-077 | negative | — | Second apply_surrender |
| test_should_commit_ledger_when_surrender_has_zero_shots | `tests/test_should_apply_surrender_when_session_active.py` | UC-005 5.6, FT-040, FT-056 | happy | — | ApplySurrender Record shots=0 |
| test_should_not_double_count_when_surrender_repeated | `tests/test_should_apply_surrender_when_session_active.py` | FT-077, FT-056, A0131 | negative | — | Нет второй записи Ledger |
| test_should_raise_when_session_missing_on_surrender | `tests/test_should_apply_surrender_when_session_active.py` | UC-005 5.4 | negative | — | SessionNotFoundError |
| test_should_reject_shot_when_surrender_already_committed | `tests/test_should_apply_surrender_when_session_active.py` | FT-077, UC-005 5.5 | negative | — | Сдача первая → выстрел SHOT_GAME_OVER |
| test_should_apply_surrender_when_shot_already_accepted | `tests/test_should_apply_surrender_when_session_active.py` | FT-077, UC-005 5.5 | edge | — | Выстрел первый → одна сдача, shots=1 |
| test_should_return_400_surrender_wrong_channel_when_post_surrender | `tests/test_should_send_game_over_when_ws_surrender.py` | A0130, A0157, OpenAPI rejectSurrenderOverRest | negative | — | REST 400 SURRENDER_WRONG_CHANNEL |
| test_should_leave_session_unchanged_when_post_surrender | `tests/test_should_send_game_over_when_ws_surrender.py` | FT-077, A0001 | negative | — | REST не меняет Active и Ledger |
| test_should_send_game_over_without_seq_when_ws_surrender_zero_shots | `tests/test_should_send_game_over_when_ws_surrender.py` | UC-005, FT-077, OpenAPI GameOverEvent | happy | — | seq omitted; Record shots=0 |
| test_should_include_seq_when_ws_surrender_after_shots | `tests/test_should_send_game_over_when_ws_surrender.py` | OpenAPI GameOverEvent | edge | — | seq = last shot |
| test_should_accept_ws_surrender_when_backend_turn | `tests/test_should_send_game_over_when_ws_surrender.py` | A0092, FT-077 | happy | — | WS сдача на ходе Backend |
| test_should_keep_session_when_ws_disconnects_without_surrender | `tests/test_should_send_game_over_when_ws_surrender.py` | A0092, FT-077, UC-005 5.3 | negative | — | Обрыв ≠ сдача |
| test_should_send_one_game_over_when_shot_then_surrender | `tests/test_should_send_game_over_when_ws_surrender.py` | FT-077, UC-005 5.5 | edge | — | Очередь shot+surrender; один gameOver и одна запись Ledger; `_collect_until_game_over` (лимит кадров + nowait хвост), не `_drain_until_close` |
| test_should_send_one_game_over_when_surrender_then_shot | `tests/test_should_send_game_over_when_ws_surrender.py` | FT-077, UC-005 5.5 | edge | — | Сдача первая; выстрел в очереди не второй исход; тот же хелпер, оракул один gameOver / один Ledger |
| test_should_emit_surrender_json_when_send_surrender | `tests/test_should_show_surrender_when_player_confirms.py` | A0130, FT-077 | happy | — | `send_surrender` → `{type: surrender}`; поток не стартует |
| test_should_fill_confirm_labels_when_surrender_dialog_presents | `tests/test_should_show_surrender_when_player_confirms.py` | A0119 | happy | dialog | `surrender-dialog` / confirm / cancel |
| test_should_open_confirm_dialog_when_surrender_clicked | `tests/test_should_show_surrender_when_player_confirms.py` | A0119 | happy | dialog | `battle-surrender`; `exec` патч; без WS до confirm |
| test_should_open_confirm_dialog_when_menu_surrender_triggered | `tests/test_should_show_surrender_when_player_confirms.py` | A0119 | happy | dialog | `menu-surrender` |
| test_should_not_send_surrender_when_confirm_cancelled | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005 5.3, A0119 | negative | dialog | `surrender-cancel`; партия Active |
| test_should_show_surrender_loading_when_confirm_accepted | `tests/test_should_show_surrender_when_player_confirms.py` | A0131, A0130 | happy | loading | `battle-surrender-loading`; кнопки disabled; нет локального итога |
| test_should_ignore_second_surrender_when_already_pending | `tests/test_should_show_surrender_when_player_confirms.py` | A0131 | edge | disabled | Повтор confirm / меню не шлёт второй кадр |
| test_should_show_surrender_error_when_channel_missing | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005 5.2 | negative | error | Нет канала; `battle-surrender-error`; `err_surrender` |
| test_should_show_surrender_error_when_channel_drops | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005 5.2, FT-077 | negative | error | `_disconnected` при pending ≠ локальный GAME_OVER |
| test_should_show_surrender_error_when_ws_rejects | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005 5.1, A0137, FT-059 | negative | error | Кадр `error` / `VALIDATION_ERROR` → `i18n.err_validation`; фаза error; экран партии; матч не завершён |
| test_should_not_send_surrender_when_window_closes | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005 E2, FT-077 | negative | — | `closeEvent`; обрыв окна ≠ кадр surrender |
| test_should_allow_surrender_when_computer_turn | `tests/test_should_show_surrender_when_player_confirms.py` | A0092, FT-077 | edge | — | Ход Компьютера; confirm → WS |
| test_should_not_send_shot_when_surrender_pending | `tests/test_should_show_surrender_when_player_confirms.py` | A0131 | edge | disabled | Клик `computer-board` не шлёт shot |
| test_should_show_result_when_surrender_game_over_arrives | `tests/test_should_show_surrender_when_player_confirms.py` | UC-005, FT-077, A0118 | happy | dialog | После loading — `gameOver` Surrender; `game-over-reason` |
| test_should_map_shots_turn_and_ttl_when_resume_snapshot_complete | `tests/test_should_apply_session_snapshot_when_resume_arrives.py` | UC-006, FT-002, FT-054, FT-080 | happy | — | `session_state_to_scene`; shots + ход Backend + remain TTL |
| test_should_raise_when_resume_snapshot_omits_ttl | `tests/test_should_apply_session_snapshot_when_resume_arrives.py` | UC-006 | negative | — | Нет `remainTtlSeconds` |
| test_should_raise_when_resume_snapshot_turn_invalid | `tests/test_should_apply_session_snapshot_when_resume_arrives.py` | UC-006 | negative | — | `turn` не Player/Backend |
| test_should_raise_when_resume_snapshot_shots_not_list | `tests/test_should_apply_session_snapshot_when_resume_arrives.py` | UC-006 | negative | — | `shots` не массив |
| test_should_reconnect_party_when_channel_disconnected | `tests/test_should_reconnect_party_when_channel_drops.py` | UC-006, US-006 AC1, FT-054, A0133 | happy | error → loading → success | `_disconnected` → таймер delay=0 → новый worker; снимок с ходом/TTL |
| test_should_show_ttl_mmss_when_battle_snapshot_bound | `tests/test_should_reconnect_party_when_channel_drops.py` | FT-080, US-006 AC3, A0120 | happy | success | `battle._ttl_label` `30:00` / `01:05` |
| test_should_leave_match_without_surrender_when_ttl_expired | `tests/test_should_reconnect_party_when_channel_drops.py` | FT-066, US-006 AC4 | negative | error | Нет WS surrender / диалога GAME_OVER; reconnect стоп |
| test_should_omit_session_id_when_qsettings_keys_listed | `tests/test_should_reconnect_party_when_channel_drops.py` | A0093, A0132, FT-054 | happy | — | QSettings без session; нет `QLineEdit` id |
| test_should_reject_incomplete_snapshot_when_session_payload_broken | `tests/test_should_reconnect_party_when_channel_drops.py` | UC-006 | negative | error | Битый `sessionSnapshot`; живая сцена не заменяется |
| test_should_stop_reconnect_when_handshake_unavailable | `tests/test_should_reconnect_party_when_channel_drops.py` | FT-067, A0001 | negative | error | `_channel_error` SESSION_UNAVAILABLE, `retry=False` |
| test_should_stop_reconnect_when_returning_to_lobby | `tests/test_should_reconnect_party_when_channel_drops.py` | UC-006, A0132 | edge | — | `_show_lobby` гасит таймер reconnect |
| test_should_set_retry_true_when_handshake_close_is_abnormal | `tests/test_should_retry_handshake_when_transport_drops.py` | UC-006 5.2 | edge | — | Мок QWebSocket; close 1006 → `_channel_error` retry=True |
| test_should_set_retry_true_when_handshake_close_is_zero | `tests/test_should_retry_handshake_when_transport_drops.py` | UC-006 5.2 | edge | — | Close 0 / RST; retry=True, не 1008 |
| test_should_set_retry_true_when_handshake_connection_refused | `tests/test_should_retry_handshake_when_transport_drops.py` | UC-006 5.2 | edge | — | `ConnectionRefusedError` на handshake; retry=True |
| test_should_set_retry_false_when_handshake_close_is_policy_violation | `tests/test_should_retry_handshake_when_transport_drops.py` | FT-067 | negative | — | Close 1008 → SESSION_UNAVAILABLE, retry=False |
| test_should_use_full_timeout_when_first_party_handshake | `tests/test_should_retry_handshake_when_transport_drops.py` | UC-002 5.2 | happy | loading | Первый `PartyChannelWorker`: 30s, не resume 4s |
| test_should_use_four_second_timeout_when_resume_handshake | `tests/test_should_retry_handshake_when_transport_drops.py` | UC-006 5.2 | happy | error → loading | Reconnect worker: `PARTY_CHANNEL_RESUME_TIMEOUT_SECONDS == 4.0` |
| test_should_switch_lobby_captions_when_language_menu_toggled | `tests/test_should_switch_interface_language_when_menu_chosen.py` | UC-008, FT-059, FT-061, A0049 | happy | success | `menu-language` RU↔EN; вкладки; «Компьютер»/Computer |
| test_should_keep_session_and_cell_codes_when_language_changes_in_battle | `tests/test_should_switch_interface_language_when_menu_chosen.py` | UC-008, FT-008, FT-073, A0091 | happy | success | Буквы А–К / A–J; журнал display; sessionId и `.code` те же; счётчики POST/WS |
| test_should_retranslate_open_dialogs_when_language_changes | `tests/test_should_switch_interface_language_when_menu_chosen.py` | NFT-016, A0049 | happy | dialog | Сдача / game-over / stats без `exec` |
| test_should_retranslate_channel_error_when_language_changes | `tests/test_should_switch_interface_language_when_menu_chosen.py` | UC-008, A0137 | negative | error | `battle-channel-error` TIMEOUT пересобирается |
| test_should_use_valid_language_when_qsettings_value_is_garbage | `tests/test_should_switch_interface_language_when_menu_chosen.py` | UC-008 5.1, FT-060 | negative | — | Мусор в ключе не остаётся; UI RU\|EN |
| test_should_apply_new_language_when_settings_write_fails | `tests/test_should_switch_interface_language_when_menu_chosen.py` | UC-008 5.2 | edge | success | `_persist` OSError; экран всё равно EN |
| test_should_use_russian_when_os_locale_is_russian | `tests/test_should_switch_interface_language_when_menu_chosen.py` | FT-060, A0029, A0136 | edge | — | Нет ключа; `locale` ru_RU |
| test_should_use_english_when_os_locale_is_not_russian | `tests/test_should_switch_interface_language_when_menu_chosen.py` | FT-060, A0029 | edge | — | Нет ключа; `locale` de_DE → EN |
| test_should_keep_stored_language_when_os_locale_differs | `tests/test_should_switch_interface_language_when_menu_chosen.py` | FT-062, A0136 | happy | success | Ключ EN важнее ОС ru |

## Пробелы (намеренно не закрыты в этом ходе)

| Пробел | Почему |
| --- | --- |
| Прогон pytest / `/use-tests` | Запрет `/new-tests`; набор не гонялся |
| Бэкенд-тесты UC-008 | Срез S-08 только фронт; API язык не хранит (A0091) |
| Смена языка при ошибке старта лобби / KPI | Канал TIMEOUT покрыт; start/stats error — тот же `_refresh_error_texts` |
| Кадр `SESSION_ABORTED` после смены языка | A0137: ключ `toast_abort` в каталоге; UI-сценарий abort — не дубль канала |
| UC-008 5.5 быстрые RU↔EN | Последний валидный язык покрыт двумя trigger в лобби |
| Живой timeout сети при reconnect (UC-006 5.2) / `PartyChannelWorker.run` | Скилл: сеть мокается; классификация close/SocketError — мок Qt; UI retry True/False уже в reconnect |
| Реальный рестарт процесса ОС (A0093) | Unit видит отсутствие persist; kill/relaunch — не этот раннер |
| UC-006 E2 гонка TTL между проверкой и снимком | Без `sleep`; не изолируется unit-ом |
| Handshake expired TTL / unknown id / GAME_OVER leftover / abort | Уже в `test_should_return_shot_events_when_party_ws.py`; не клонировали |
| UC-005 5.1 невалидный WS payload на сервере | Клиент ловит кадр `error`; отказ бэкенда — в API-срезе |
| Живой timeout сети при сдаче (urllib/QWebSocket) | Скилл: сеть мокается; UI error — `_channel_error` / `_disconnected` |
| UC-005 E1 кадр gameOver не доставлен | Исход уже на сервере; reconnect = FT-067 / UC-006 |
| UC-004 5.2 обрыв Фронтенда во время `gameOver` | Исход уже на сервере; reconnect = FT-067 |
| UC-004 5.4 POST статистики с клиента | Закрыто в S-02 (`405`); не дублировали |
| Живой Redis Lua `record_outcome` / Docker | Скилл: мок порта; FakeRedis eval эмулирует SISMEMBER |
| NFT p95 конца партии | Нагрузка, не unit |
| Бэкенд-тесты состава флота S-04-1 | Срез только клиент+UI; бэкенд в S-04-1 не входил |
| Пиксели букв `paintEvent` поля | Unit смотрит `board.language` + `letters_for`, не raster |
| UC-003 5.2 обрыв Фронтенда во время оповещения | Состояние уже на сервере; UC-006 reconnect — не этот срез |
| UC-003 E2 ошибка формирования кадра после выстрела | Persist error на use case есть; сбой send после apply — не изолирован |
| NFT-002 p95 ≤ 200 мс heatmap | Нагрузка MR-04, не unit |
| UC-007 GET /statistics live Redis / Docker | Скилл: мок порта; HASH+LIST читаются через FakeRedis |
| UC-007 5.3 close во время loading | Не этот срез |
| Реальный рестарт процесса после FT-062 | Unit читает изолированный ini; kill/relaunch ОС — не этот раннер |
| Живой старт UI: 503 `SESSION_START_FAILED`, close во время loading (UC-001 5.3) | Вне явного списка ПМ для S-01 |
| Реальный `CreateSessionWorker.run` / живой POST | Запрет скилла: сеть мокается |
| Живой `GetStatisticsWorker.start` / GET /statistics | Запрет скилла: сеть мокается; `run()` покрыт с моком |
| `QDialog.exec` / `show()` окна статистики | Запрет `QApplication.exec`; `exec` патчится |
| NFT-015 p95 измерение (≥100 созданий) | Нагрузочный критерий, не unit |
| HTTP 404/409 JSON на WS upgrade | Close 1008; канон OpenAPI HTTP — known issue G-01 |
| FT-048 выстрел по своему полю | Команда `shot` всегда бьёт поле Бэкенда |
| Живой QWebSocket / `PartyChannelWorker.run` | Запрет скилла: сеть мокается |
| UC-002 5.2 timeout ответа на уже отправленный выстрел | Handshake timeout покрыт; silent after send — не этот список |
| REST POST /shots из окна | Клиент его не вызывает; отказ REST — бэкенд-тесты |
| UC-008 5.3 закрытие меню без выбора | Нет побочного эффекта; не отдельный unit |
| FT-069 выстрел до старта | После UC-001 сессия уже с ходом Игрока |
| WS FT-045 / FT-047 | Домен покрыт; на канале после `gameOver` цикл рвётся, JSON удалён |
| NFT-001 / NFT-006 p95 выстрела и отказа | Нагрузка, не unit |
