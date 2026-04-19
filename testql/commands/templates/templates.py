"""TestQL test file templates."""

from __future__ import annotations


API_TEMPLATE = '''\
meta:
  name: "API Health Check"
  type: api
  tags: [smoke, api, health]

SET api_url = "${api_url:-http://localhost:8101}"

# Health check
GET "${api_url}/api/health"
ASSERT_STATUS 200
ASSERT_JSON path="status" equals="ok"

LOG "API health check passed"
'''


GUI_TEMPLATE = '''\
meta:
  name: "GUI Navigation Test"
  type: gui
  tags: [smoke, gui, navigation]

SET base_url = "${base_url:-http://localhost:8100}"

# Navigate to home
NAVIGATE "${base_url}/"
WAIT 500

# Check main elements
ASSERT_TITLE "contains" "Home"
ASSERT_SELECTOR "nav" "exists"

LOG "Navigation test passed"
'''


ENCODER_TEMPLATE = '''\
meta:
  name: "Encoder Basic Test"
  type: encoder
  tags: [smoke, encoder]

SET encoder_url = "${encoder_url:-http://localhost:8105}"

# Encoder operations
ENCODER_ON
WAIT 200
ENCODER_STATUS
ASSERT_ENCODER "active"
ENCODER_OFF

LOG "Encoder test passed"
'''
