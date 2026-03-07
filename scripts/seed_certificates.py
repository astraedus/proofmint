"""
Seed 10 diverse certificates via the ProofMint API.
Each triggers a real code review -> HCS publish -> NFT mint on Hedera testnet.

Usage: python scripts/seed_certificates.py [--api-url http://localhost:8001]
"""
import argparse
import time
import requests

SNIPPETS = [
    # 1. Critical: eval
    {
        "code": """def process_user_input(user_data):
    result = eval(user_data)
    return result""",
        "language": "python",
    },
    # 2. Critical: hardcoded password
    {
        "code": """import psycopg2

def connect_db():
    password = "super_secret_p4ssw0rd!"
    conn = psycopg2.connect(host="db.prod.internal", password=password)
    return conn""",
        "language": "python",
    },
    # 3. Critical: SQL injection
    {
        "code": """import sqlite3

def get_user(username):
    conn = sqlite3.connect("app.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return conn.execute(query).fetchone()""",
        "language": "python",
    },
    # 4. Critical: shell injection
    {
        "code": """import os

def convert_file(filename):
    os.system(f"ffmpeg -i {filename} output.mp4")
    return "output.mp4"
""",
        "language": "python",
    },
    # 5. Clean: Python utility
    {
        "code": """from dataclasses import dataclass
from typing import Optional
import hashlib

@dataclass
class Document:
    title: str
    content: str
    author: Optional[str] = None

    def content_hash(self) -> str:
        return hashlib.sha256(self.content.encode()).hexdigest()

    def word_count(self) -> int:
        return len(self.content.split())
""",
        "language": "python",
    },
    # 6. Clean: TypeScript React component
    {
        "code": """interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export function Button({ label, onClick, variant = 'primary', disabled = false }: ButtonProps) {
  const baseClasses = 'px-4 py-2 rounded-lg font-medium transition-colors';
  const variantClasses = variant === 'primary'
    ? 'bg-blue-600 hover:bg-blue-500 text-white'
    : 'bg-gray-200 hover:bg-gray-300 text-gray-800';

  return (
    <button
      className={`${baseClasses} ${variantClasses}`}
      onClick={onClick}
      disabled={disabled}
    >
      {label}
    </button>
  );
}
""",
        "language": "typescript",
    },
    # 7. Clean: Rust struct
    {
        "code": """use std::collections::HashMap;

pub struct Config {
    settings: HashMap<String, String>,
}

impl Config {
    pub fn new() -> Self {
        Config {
            settings: HashMap::new(),
        }
    }

    pub fn set(&mut self, key: &str, value: &str) {
        self.settings.insert(key.to_string(), value.to_string());
    }

    pub fn get(&self, key: &str) -> Option<&String> {
        self.settings.get(key)
    }
}
""",
        "language": "rust",
    },
    # 8. Minor: bare except
    {
        "code": """import json
import logging

logger = logging.getLogger(__name__)

def parse_config(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        logger.error("Failed to parse config")
        return {}
""",
        "language": "python",
    },
    # 9. Minor: TODO + wildcard import
    {
        "code": """from os.path import *
import logging

# TODO: refactor this to use pathlib
def find_files(directory, extension):
    results = []
    for name in listdir(directory):
        full = join(directory, name)
        if isfile(full) and name.endswith(extension):
            results.append(full)
    return results
""",
        "language": "python",
    },
    # 10. Critical: SSL verify disabled + debug mode
    {
        "code": """import requests

DEBUG = True

def fetch_api_data(url, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()
""",
        "language": "python",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://localhost:8001")
    args = parser.parse_args()

    base = args.api_url.rstrip("/")
    endpoint = f"{base}/api/tasks/review"

    print(f"Seeding {len(SNIPPETS)} certificates to {endpoint}...")

    for i, snippet in enumerate(SNIPPETS, 1):
        print(f"\n[{i}/{len(SNIPPETS)}] Submitting {snippet['language']} snippet...")
        try:
            r = requests.post(endpoint, json=snippet, timeout=60)
            r.raise_for_status()
            data = r.json()
            verdict = data.get("verdict", "?")
            nft = data.get("nft_serial_number", "?")
            hcs = data.get("hcs_sequence_number", "?")
            print(f"  -> Verdict: {verdict} | NFT #{nft} | HCS seq {hcs}")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        if i < len(SNIPPETS):
            print("  Waiting 2s for Hedera indexing...")
            time.sleep(2)

    print(f"\nDone! Check {base}/ for the gallery.")


if __name__ == "__main__":
    main()
