v0.5.0
- Fixed 4 tools calling dead REST paths (get_iv_radar, get_equity_curves, generate_stock_images, generate_stock_research_report all 404'd)
- Server now delegates every HTTP call to the hpsilab-mcp SDK instead of hand-rolled requests calls, so endpoint paths have one source of truth
- Added readOnlyHint/destructiveHint/openWorldHint tool annotations to all 9 tools

v0.4.1
- Added get_pretrade_risk_scan