# -*- coding: utf-8 -*-
# scripts/mask_keys.py
import re
import sys
from pathlib import Path

SKIP_FILES = {
    'mask_keys.py',
    '.pre-commit-config.yaml',
    'package-lock.json',
    'yarn.lock',
}

SKIP_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico',
    '.svg', '.woff', '.woff2', '.ttf', '.eot',
    '.zip', '.tar', '.gz', '.lock', '.bin',
    '.class', '.jar', '.exe', '.so', '.a',
}

SECRET_PATTERNS = [
    (
        r'(FIREBASE_API_KEY'
        r'|FIREBASE_AUTH_DOMAIN'
        r'|FIREBASE_PROJECT_ID'
        r'|FIREBASE_STORAGE_BUCKET'
        r'|FIREBASE_MESSAGING_SENDER_ID'
        r'|FIREBASE_APP_ID'
        r'|FIREBASE_MEASUREMENT_ID'
        r'|API_KEY'
        r'|API_SECRET'
        r'|APP_SECRET'
        r'|AUTH_TOKEN'
        r'|ACCESS_TOKEN'
        r'|REFRESH_TOKEN'
        r'|SECRET_KEY'
        r'|PRIVATE_KEY'
        r'|CLIENT_SECRET'
        r'|CLIENT_ID'
        r'|DATABASE_URL'
        r'|DATABASE_PASSWORD'
        r'|DB_PASSWORD'
        r'|DB_USER'
        r'|SMTP_PASSWORD'
        r'|SENDGRID_API_KEY'
        r'|STRIPE_SECRET_KEY'
        r'|STRIPE_PUBLISHABLE_KEY'
        r'|AWS_ACCESS_KEY_ID'
        r'|AWS_SECRET_ACCESS_KEY'
        r'|GOOGLE_CLIENT_SECRET'
        r'|GITHUB_TOKEN'
        r'|JWT_SECRET'
        r'|ENCRYPTION_KEY'
        r'|PASSWORD)'
        r'=[^\s\n"' + "'" + r'`]+'
    ),
]

masked_files = []
files_to_scan = sys.argv[1:] if len(sys.argv) > 1 else []

for file_str in files_to_scan:
    file_path = Path(file_str)
    if not file_path.is_file():
        continue
    if file_path.name in SKIP_FILES:
        continue
    if file_path.suffix.lower() in SKIP_EXTENSIONS:
        continue
    try:
        content = file_path.read_text(errors='ignore')
    except Exception:
        continue
    original = content
    for pattern in SECRET_PATTERNS:
        content = re.sub(
            pattern,
            lambda m: m.group(0).split('=')[0] + '=******',
            content,
        )
    if content != original:
        file_path.write_text(content)
        masked_files.append(str(file_path))

if masked_files:
    msg = '[MASKED] Secrets found in: ' + ', '.join(masked_files)
    sys.stdout.buffer.write(msg.encode('utf-8') + b'\n')
    sys.stdout.buffer.write(
        b'[ACTION] Review changes, re-stage and commit again.\n'
    )
    sys.exit(1)
else:
    sys.stdout.buffer.write(b'[OK] No secrets found.\n')
    sys.exit(0)
