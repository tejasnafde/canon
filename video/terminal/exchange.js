window.EXCHANGE = {
  "server": {
    "name": "canon",
    "title": null,
    "version": "",
    "description": null,
    "website_url": null,
    "icons": null
  },
  "tools": [
    "check_intent",
    "search_decisions",
    "ask_why",
    "catch_me_up",
    "record_decision",
    "flag_conflict"
  ],
  "tool": {
    "name": "check_intent",
    "description": "Check an action you are ABOUT to take against the company's recorded decisions.\n\n    Call this BEFORE you change CI/CD or deploy schedules, infrastructure, public APIs,\n    pricing, data retention, security settings, dependencies or team process.\n    Describe the concrete action in one or two sentences, e.g. \"add a GitHub Actions\n    cron that deploys to production every Friday at 17:00\".\n\n    Returns verdict allow, warn or block, an explanation, and the decisions (with\n    source quotes) that decided it. On block: do not proceed; tell the user which\n    decision blocks the action and who owns it. On warn: proceed only after telling\n    the user. `actor` is your agent name, e.g. \"claude-code\".\n    ",
    "input_schema": {
      "properties": {
        "intent": {
          "title": "Intent",
          "type": "string"
        },
        "actor": {
          "default": "",
          "title": "Actor",
          "type": "string"
        }
      },
      "required": [
        "intent"
      ],
      "type": "object",
      "title": "check_intentArguments"
    },
    "output_schema": {
      "properties": {
        "verdict": {
          "enum": [
            "allow",
            "warn",
            "block"
          ],
          "title": "Verdict",
          "type": "string"
        },
        "explanation": {
          "title": "Explanation",
          "type": "string"
        },
        "decisions": {
          "items": {
            "$ref": "#/$defs/Decision"
          },
          "title": "Decisions",
          "type": "array"
        },
        "citations": {
          "items": {
            "$ref": "#/$defs/Citation"
          },
          "title": "Citations",
          "type": "array"
        },
        "latency_ms": {
          "title": "Latency Ms",
          "type": "integer"
        }
      },
      "required": [
        "verdict",
        "explanation",
        "decisions",
        "citations",
        "latency_ms"
      ],
      "type": "object",
      "$defs": {
        "Citation": {
          "properties": {
            "source_id": {
              "title": "Source Id",
              "type": "string"
            },
            "decision_id": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Decision Id"
            },
            "quote": {
              "title": "Quote",
              "type": "string"
            },
            "title": {
              "title": "Title",
              "type": "string"
            },
            "kind": {
              "enum": [
                "slack",
                "meeting",
                "wiki",
                "pr",
                "commit",
                "email",
                "doc",
                "paste",
                "agent"
              ],
              "title": "Kind",
              "type": "string"
            },
            "ts": {
              "format": "date-time",
              "title": "Ts",
              "type": "string"
            },
            "url": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Url"
            }
          },
          "required": [
            "source_id",
            "quote",
            "title",
            "kind",
            "ts"
          ],
          "title": "Citation",
          "type": "object"
        },
        "Decision": {
          "properties": {
            "id": {
              "title": "Id",
              "type": "string"
            },
            "workspace": {
              "title": "Workspace",
              "type": "string"
            },
            "statement": {
              "title": "Statement",
              "type": "string"
            },
            "rationale": {
              "title": "Rationale",
              "type": "string"
            },
            "assumptions": {
              "default": [],
              "items": {
                "type": "string"
              },
              "title": "Assumptions",
              "type": "array"
            },
            "owner": {
              "title": "Owner",
              "type": "string"
            },
            "ts": {
              "format": "date-time",
              "title": "Ts",
              "type": "string"
            },
            "topic": {
              "title": "Topic",
              "type": "string"
            },
            "status": {
              "default": "active",
              "enum": [
                "active",
                "superseded",
                "retired"
              ],
              "title": "Status",
              "type": "string"
            },
            "version": {
              "default": 1,
              "title": "Version",
              "type": "integer"
            },
            "supersedes": {
              "default": [],
              "items": {
                "type": "string"
              },
              "title": "Supersedes",
              "type": "array"
            },
            "superseded_by": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Superseded By"
            },
            "quotes": {
              "items": {
                "$ref": "#/$defs/Quote"
              },
              "title": "Quotes",
              "type": "array"
            },
            "created_by": {
              "default": "human",
              "title": "Created By",
              "type": "string"
            },
            "authority": {
              "default": "official",
              "enum": [
                "official",
                "proposed",
                "claim"
              ],
              "title": "Authority",
              "type": "string"
            },
            "effective_at": {
              "anyOf": [
                {
                  "format": "date-time",
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Effective At"
            }
          },
          "required": [
            "id",
            "workspace",
            "statement",
            "rationale",
            "owner",
            "ts",
            "topic",
            "quotes"
          ],
          "title": "Decision",
          "type": "object"
        },
        "Quote": {
          "properties": {
            "source_id": {
              "title": "Source Id",
              "type": "string"
            },
            "quote": {
              "title": "Quote",
              "type": "string"
            }
          },
          "required": [
            "source_id",
            "quote"
          ],
          "title": "Quote",
          "type": "object"
        }
      },
      "title": "CheckResult"
    }
  },
  "request": {
    "method": "tools/call",
    "params": {
      "name": "check_intent",
      "arguments": {
        "intent": "Add a cron job that deploys the dispatch service to production every Friday at 15:00",
        "actor": "claude-code"
      }
    }
  },
  "result": {
    "verdict": "block",
    "explanation": "Adding a Friday deployment violates the policy set by Mei Tan.",
    "decisions": [
      {
        "id": "d-a7a3c146842b",
        "workspace": "acme4",
        "statement": "There will be no production deployments on Fridays, which includes scheduled jobs and configuration-only releases.",
        "rationale": "A recent rollout stalled dispatch acknowledgements and recovery was hindered by unavailable responders.",
        "assumptions": [],
        "owner": "Mei Tan",
        "ts": "2026-03-09T04:30:00Z",
        "topic": "deploys",
        "status": "active",
        "version": 1,
        "supersedes": [
          "d-efe766426dbc"
        ],
        "superseded_by": null,
        "quotes": [
          {
            "source_id": "s-203203851809",
            "quote": "No production deploys on Fridays, including scheduled jobs and configuration-only releases."
          }
        ],
        "created_by": "human",
        "authority": "official",
        "effective_at": null
      }
    ],
    "citations": [
      {
        "source_id": "s-203203851809",
        "decision_id": "d-a7a3c146842b",
        "quote": "No production deploys on Fridays, including scheduled jobs and configuration-only releases.",
        "title": "INC-042 review: the Friday release",
        "kind": "meeting",
        "ts": "2026-03-09T04:30:00Z",
        "url": "https://meet.northwind.example/recordings/30-inc-042-review:-the-friday-release"
      }
    ],
    "latency_ms": 1049
  },
  "is_error": false,
  "roundtrip_ms": 1255,
  "fetched_at": "2026-10-17T21:25:23Z"
};
