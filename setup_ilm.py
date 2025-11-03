#!/usr/bin/env python3
"""
Elasticsearch ILM (Index Lifecycle Management) 설정 스크립트

Hot → Warm → Cold → Delete 자동 로그 관리 정책을 설정합니다.
"""

from elasticsearch import Elasticsearch
import json
import time

ES_HOST = "http://localhost:9200"
POLICY_NAME = "logs-mini-dify-policy"
INDEX_TEMPLATE_NAME = "logs-mini-dify-template"

def wait_for_elasticsearch(es, max_retries=30):
    """Elasticsearch 연결 대기"""
    print("Waiting for Elasticsearch...")
    for i in range(max_retries):
        try:
            if es.ping():
                print("✅ Elasticsearch is ready!")
                return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: Waiting... ({str(e)})")
            time.sleep(2)
    return False

def create_ilm_policy(es):
    """ILM 정책 생성"""
    policy = {
        "policy": {
            "phases": {
                "hot": {
                    "min_age": "0ms",
                    "actions": {
                        "rollover": {
                            "max_size": "5GB",
                            "max_age": "7d"
                        },
                        "set_priority": {
                            "priority": 100
                        }
                    }
                },
                "warm": {
                    "min_age": "7d",
                    "actions": {
                        "shrink": {
                            "number_of_shards": 1
                        },
                        "forcemerge": {
                            "max_num_segments": 1
                        },
                        "set_priority": {
                            "priority": 50
                        }
                    }
                },
                "cold": {
                    "min_age": "30d",
                    "actions": {
                        "freeze": {},
                        "set_priority": {
                            "priority": 0
                        }
                    }
                },
                "delete": {
                    "min_age": "90d",
                    "actions": {
                        "delete": {}
                    }
                }
            }
        }
    }

    try:
        es.ilm.put_lifecycle(name=POLICY_NAME, body=policy)
        print(f"✅ ILM Policy '{POLICY_NAME}' created successfully!")
        print(json.dumps(policy, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"❌ Failed to create ILM policy: {str(e)}")
        return False

def create_index_template(es):
    """인덱스 템플릿 생성"""
    template = {
        "index_patterns": ["logs-mini-dify-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "index.lifecycle.name": POLICY_NAME,
                "index.lifecycle.rollover_alias": "logs-mini-dify"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "log.level": {"type": "keyword"},
                    "log.logger": {"type": "keyword"},
                    "log.function": {"type": "text"},
                    "log.message": {"type": "text"},
                    "message": {"type": "text"},
                    "service": {"type": "keyword"},
                    "log_type": {"type": "keyword"},
                    "host.name": {"type": "keyword"}
                }
            }
        }
    }

    try:
        es.indices.put_index_template(name=INDEX_TEMPLATE_NAME, body=template)
        print(f"✅ Index Template '{INDEX_TEMPLATE_NAME}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create index template: {str(e)}")
        return False

def create_initial_index(es):
    """초기 인덱스 생성 (Rollover를 위한 별칭 설정)"""
    index_name = "logs-mini-dify-000001"
    alias_name = "logs-mini-dify"

    try:
        if not es.indices.exists(index=index_name):
            es.indices.create(
                index=index_name,
                body={
                    "aliases": {
                        alias_name: {
                            "is_write_index": True
                        }
                    }
                }
            )
            print(f"✅ Initial index '{index_name}' created with alias '{alias_name}'!")
        else:
            print(f"ℹ️  Index '{index_name}' already exists")
        return True
    except Exception as e:
        print(f"❌ Failed to create initial index: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🚀 Elasticsearch ILM Setup for Mini-Dify Logs")
    print("=" * 80)

    es = Elasticsearch([ES_HOST])

    if not wait_for_elasticsearch(es):
        print("❌ Failed to connect to Elasticsearch")
        return

    print("\n📋 Creating ILM Policy...")
    create_ilm_policy(es)

    print("\n📋 Creating Index Template...")
    create_index_template(es)

    print("\n📋 Creating Initial Index...")
    create_initial_index(es)

    print("\n" + "=" * 80)
    print("✅ Setup completed successfully!")
    print("=" * 80)
    print("\n📊 ILM Policy Summary:")
    print("  - Hot Phase:  0-7 days    (최근 로그, 빠른 검색)")
    print("  - Warm Phase: 7-30 days   (읽기 전용, 압축)")
    print("  - Cold Phase: 30-90 days  (거의 안 봄, 동결)")
    print("  - Delete:     90+ days    (자동 삭제)")
    print("\n🎯 Next Steps:")
    print("  1. docker-compose up -d")
    print("  2. Open Kibana: http://localhost:5601")
    print("  3. Create Index Pattern: logs-mini-dify-*")
    print("=" * 80)

if __name__ == "__main__":
    main()
