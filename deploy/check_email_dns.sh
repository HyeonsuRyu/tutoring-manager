#!/bin/sh
# FR-OPS-05: remind operators to verify SPF/DKIM when using Resend in production.
set -eu
DOMAIN="${1:-${DOMAIN:-}}"
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "local" ]; then
  echo "Skip DNS check: DOMAIN not set or local"
  exit 0
fi
echo "Check SPF/DKIM/DMARC for: $DOMAIN"
echo "  https://mxtoolbox.com/SuperTool.aspx?action=spf%3a$DOMAIN"
echo "  Resend dashboard: domain verification"
echo "See docs/email-deliverability.md"
