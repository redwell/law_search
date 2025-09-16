"""
設定読み込みユーティリティ
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """設定読み込みクラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定読み込みクラスの初期化
        
        Args:
            config_file: 設定ファイルのパス（省略時は環境に応じて自動選択）
        """
        # 環境変数ファイルの読み込み
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        
        # 設定ファイルの決定
        if config_file is None:
            env = os.getenv("ENV", "development")
            config_file = f"config/{env}.yaml"
        
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """設定ファイルの読み込み"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            print(f"⚠️  設定ファイルが見つかりません: {config_file}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応）
            default: デフォルト値
            
        Returns:
            設定値
        """
        # 環境変数を優先
        env_value = os.getenv(key.upper())
        if env_value is not None:
            return self._convert_type(env_value)
        
        # 設定ファイルから取得
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def _convert_type(self, value: str) -> Any:
        """文字列を適切な型に変換"""
        # ブール値
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数値
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # リスト（カンマ区切り）
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # 文字列
        return value
    
    def get_database_url(self) -> str:
        """データベースURLを取得"""
        return self.get("DATABASE_URL", "arangodb://root:password@localhost:8529")
    
    def get_openai_api_key(self) -> str:
        """OpenAI APIキーを取得"""
        api_key = self.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        return api_key
    
    def get_embedding_model(self) -> str:
        """埋め込みモデル名を取得"""
        return self.get("EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
    
    def get_log_level(self) -> str:
        """ログレベルを取得"""
        return self.get("LOG_LEVEL", "INFO")
    
    def is_debug(self) -> bool:
        """デバッグモードかどうか"""
        return self.get("DEBUG", False)
    
    def get_cors_origins(self) -> list:
        """CORS許可オリジンを取得"""
        return self.get("CORS_ORIGINS", ["http://localhost:3000", "http://localhost:8000"])
    
    def get_search_weights(self) -> Dict[str, float]:
        """ハイブリッド検索の重みを取得"""
        weights_str = self.get("HYBRID_SEARCH_WEIGHTS", '{"fulltext": 0.4, "vector": 0.4, "graph": 0.2}')
        try:
            import json
            return json.loads(weights_str)
        except (json.JSONDecodeError, TypeError):
            return {"fulltext": 0.4, "vector": 0.4, "graph": 0.2}
    
    def get_egov_config(self) -> Dict[str, Any]:
        """e-Gov設定を取得"""
        return {
            "base_url": self.get("EGOV_BASE_URL", "https://elaws.e-gov.go.jp"),
            "data_dir": self.get("EGOV_DATA_DIR", "./data/egov"),
            "update_interval": self.get("EGOV_UPDATE_INTERVAL", 86400)
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """セキュリティ設定を取得"""
        return {
            "secret_key": self.get("SECRET_KEY", "your-secret-key-here"),
            "rate_limit_per_minute": self.get("RATE_LIMIT_PER_MINUTE", 60),
            "max_query_length": self.get("MAX_QUERY_LENGTH", 500)
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """監視設定を取得"""
        return {
            "enable_metrics": self.get("ENABLE_METRICS", True),
            "metrics_port": self.get("METRICS_PORT", 9090)
        }
    
    def validate_config(self) -> bool:
        """設定の妥当性を検証"""
        required_keys = [
            "DATABASE_URL",
            "OPENAI_API_KEY"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 必須の設定が不足しています: {', '.join(missing_keys)}")
            return False
        
        print("✅ 設定の検証が完了しました")
        return True
    
    def print_config(self) -> None:
        """設定の表示（デバッグ用）"""
        print("📋 現在の設定:")
        print(f"  - データベースURL: {self.get_database_url()}")
        print(f"  - 埋め込みモデル: {self.get_embedding_model()}")
        print(f"  - ログレベル: {self.get_log_level()}")
        print(f"  - デバッグモード: {self.is_debug()}")
        print(f"  - CORS許可オリジン: {self.get_cors_origins()}")
        print(f"  - 検索重み: {self.get_search_weights()}")


# グローバル設定インスタンス
config = ConfigLoader()
