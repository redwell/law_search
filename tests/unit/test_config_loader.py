"""
設定ローダーのテスト
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.core.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """ConfigLoaderのテストクラス"""
    
    def test_init_with_default_config(self):
        """デフォルト設定での初期化テスト"""
        config = ConfigLoader()
        assert config is not None
        assert isinstance(config._config, dict)
    
    def test_init_with_custom_config(self):
        """カスタム設定ファイルでの初期化テスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("test_key: test_value\n")
            f.flush()
            
            config = ConfigLoader(f.name)
            assert config.get("test_key") == "test_value"
            
            os.unlink(f.name)
    
    def test_get_existing_key(self):
        """既存キーの取得テスト"""
        config = ConfigLoader()
        # 環境変数を設定
        os.environ["TEST_KEY"] = "test_value"
        
        try:
            assert config.get("TEST_KEY") == "test_value"
        finally:
            # 環境変数をクリーンアップ
            if "TEST_KEY" in os.environ:
                del os.environ["TEST_KEY"]
    
    def test_get_nonexistent_key(self):
        """存在しないキーの取得テスト"""
        config = ConfigLoader()
        assert config.get("NONEXISTENT_KEY") is None
        assert config.get("NONEXISTENT_KEY", "default") == "default"
    
    def test_get_nested_key(self):
        """ネストしたキーの取得テスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
nested:
  key:
    value: "test_value"
""")
            f.flush()
            
            config = ConfigLoader(f.name)
            assert config.get("nested.key.value") == "test_value"
            
            os.unlink(f.name)
    
    def test_convert_type_boolean(self):
        """型変換テスト（ブール値）"""
        config = ConfigLoader()
        assert config._convert_type("true") is True
        assert config._convert_type("false") is False
        assert config._convert_type("TRUE") is True
        assert config._convert_type("FALSE") is False
    
    def test_convert_type_number(self):
        """型変換テスト（数値）"""
        config = ConfigLoader()
        assert config._convert_type("123") == 123
        assert config._convert_type("123.45") == 123.45
        assert config._convert_type("-123") == -123
    
    def test_convert_type_list(self):
        """型変換テスト（リスト）"""
        config = ConfigLoader()
        assert config._convert_type("a,b,c") == ["a", "b", "c"]
        assert config._convert_type("a, b, c") == ["a", "b", "c"]
    
    def test_convert_type_string(self):
        """型変換テスト（文字列）"""
        config = ConfigLoader()
        assert config._convert_type("hello") == "hello"
        assert config._convert_type("123abc") == "123abc"
    
    def test_get_database_url(self):
        """データベースURL取得テスト"""
        config = ConfigLoader()
        # 環境変数を設定
        os.environ["DATABASE_URL"] = "arangodb://test:test@localhost:8529"
        
        try:
            assert config.get_database_url() == "arangodb://test:test@localhost:8529"
        finally:
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
    
    def test_get_openai_api_key(self):
        """OpenAI APIキー取得テスト"""
        config = ConfigLoader()
        # 環境変数を設定
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
        try:
            assert config.get_openai_api_key() == "test_api_key"
        finally:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
    
    def test_get_openai_api_key_missing(self):
        """OpenAI APIキー未設定テスト"""
        config = ConfigLoader()
        # 環境変数をクリア
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        with pytest.raises(ValueError, match="OPENAI_API_KEYが設定されていません"):
            config.get_openai_api_key()
    
    def test_get_embedding_model(self):
        """埋め込みモデル取得テスト"""
        config = ConfigLoader()
        assert config.get_embedding_model() == "jinaai/jina-embeddings-v3"
        
        # 環境変数を設定
        os.environ["EMBEDDING_MODEL"] = "test-model"
        
        try:
            assert config.get_embedding_model() == "test-model"
        finally:
            if "EMBEDDING_MODEL" in os.environ:
                del os.environ["EMBEDDING_MODEL"]
    
    def test_get_log_level(self):
        """ログレベル取得テスト"""
        config = ConfigLoader()
        assert config.get_log_level() == "INFO"
        
        # 環境変数を設定
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        try:
            assert config.get_log_level() == "DEBUG"
        finally:
            if "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]
    
    def test_is_debug(self):
        """デバッグモード判定テスト"""
        config = ConfigLoader()
        assert config.is_debug() is False
        
        # 環境変数を設定
        os.environ["DEBUG"] = "true"
        
        try:
            assert config.is_debug() is True
        finally:
            if "DEBUG" in os.environ:
                del os.environ["DEBUG"]
    
    def test_get_cors_origins(self):
        """CORS許可オリジン取得テスト"""
        config = ConfigLoader()
        expected = ["http://localhost:3000", "http://localhost:8000"]
        assert config.get_cors_origins() == expected
        
        # 環境変数を設定
        os.environ["CORS_ORIGINS"] = "http://test1,http://test2"
        
        try:
            assert config.get_cors_origins() == ["http://test1", "http://test2"]
        finally:
            if "CORS_ORIGINS" in os.environ:
                del os.environ["CORS_ORIGINS"]
    
    def test_get_search_weights(self):
        """検索重み取得テスト"""
        config = ConfigLoader()
        expected = {"fulltext": 0.4, "vector": 0.4, "graph": 0.2}
        assert config.get_search_weights() == expected
        
        # 環境変数を設定
        os.environ["HYBRID_SEARCH_WEIGHTS"] = '{"fulltext": 0.5, "vector": 0.3, "graph": 0.2}'
        
        try:
            expected = {"fulltext": 0.5, "vector": 0.3, "graph": 0.2}
            assert config.get_search_weights() == expected
        finally:
            if "HYBRID_SEARCH_WEIGHTS" in os.environ:
                del os.environ["HYBRID_SEARCH_WEIGHTS"]
    
    def test_get_egov_config(self):
        """e-Gov設定取得テスト"""
        config = ConfigLoader()
        egov_config = config.get_egov_config()
        
        assert "base_url" in egov_config
        assert "data_dir" in egov_config
        assert "update_interval" in egov_config
        assert egov_config["base_url"] == "https://elaws.e-gov.go.jp"
    
    def test_get_security_config(self):
        """セキュリティ設定取得テスト"""
        config = ConfigLoader()
        security_config = config.get_security_config()
        
        assert "secret_key" in security_config
        assert "rate_limit_per_minute" in security_config
        assert "max_query_length" in security_config
        assert security_config["rate_limit_per_minute"] == 60
    
    def test_get_monitoring_config(self):
        """監視設定取得テスト"""
        config = ConfigLoader()
        monitoring_config = config.get_monitoring_config()
        
        assert "enable_metrics" in monitoring_config
        assert "metrics_port" in monitoring_config
        assert monitoring_config["enable_metrics"] is True
    
    def test_validate_config_success(self):
        """設定検証成功テスト"""
        config = ConfigLoader()
        # 必要な環境変数を設定
        os.environ["DATABASE_URL"] = "arangodb://test:test@localhost:8529"
        os.environ["OPENAI_API_KEY"] = "test_api_key"
        
        try:
            assert config.validate_config() is True
        finally:
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
    
    def test_validate_config_failure(self):
        """設定検証失敗テスト"""
        config = ConfigLoader()
        # 必要な環境変数をクリア
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        assert config.validate_config() is False
