"""
データパーサーモジュールのテスト
"""

import pytest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from src.core.data.parser import XMLParser, DataPreprocessor, Article, LawDocument


class TestXMLParser:
    """XMLParserのテストクラス"""
    
    @pytest.fixture
    def temp_xml_file(self):
        """一時XMLファイルのフィクスチャ"""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<law xmlns="http://elaws.e-gov.go.jp/XMLSchema">
    <LawTitle>所得税法</LawTitle>
    <LawTitleKana>しょとくぜいほう</LawTitleKana>
    <LawNum>昭和32年法律第89号</LawNum>
    <PromulgateDate>1957-03-31</PromulgateDate>
    <EffectiveDate>1957-04-01</EffectiveDate>
    <Article>
        <ArticleNum>第1条</ArticleNum>
        <ArticleCaption>この法律は、個人の所得に係る税金について定める。</ArticleCaption>
    </Article>
    <Article>
        <ArticleNum>第2条</ArticleNum>
        <ArticleCaption>所得とは、個人の収入から必要経費を差し引いた金額をいう。</ArticleCaption>
    </Article>
</law>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            f.flush()
            yield f.name
        
        # クリーンアップ
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def parser(self):
        """XMLパーサーのフィクスチャ"""
        return XMLParser()
    
    def test_init(self, parser):
        """初期化テスト"""
        assert parser is not None
        assert parser.namespaces is not None
        assert 'law' in parser.namespaces
    
    def test_parse_law_xml_success(self, parser, temp_xml_file):
        """法律XMLパース成功テスト"""
        result = parser.parse_law_xml(temp_xml_file)
        
        assert result is not None
        assert isinstance(result, LawDocument)
        # ファイル名から推測されるID（一時ファイル名）
        assert result.law_id is not None
        assert result.law_name == "所得税法"
        assert result.law_name_kana == "しょとくぜいほう"
        assert result.law_number == "昭和32年法律第89号"
        assert result.promulgation_date == "1957-03-31"
        assert result.effective_date == "1957-04-01"
        assert result.category == "税法"
        assert len(result.articles) == 2
        
        # 条文の確認
        article1 = result.articles[0]
        assert article1.article_number == "第1条"
        assert "個人の所得に係る税金について定める" in article1.content
        
        article2 = result.articles[1]
        assert article2.article_number == "第2条"
        assert "所得とは、個人の収入から必要経費を差し引いた金額をいう" in article2.content
    
    def test_parse_law_xml_invalid_file(self, parser):
        """無効なXMLファイルパーステスト"""
        result = parser.parse_law_xml("nonexistent.xml")
        assert result is None
    
    def test_parse_law_xml_malformed_xml(self, parser):
        """不正なXMLファイルパーステスト"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("invalid xml content")
            f.flush()
            
            result = parser.parse_law_xml(f.name)
            assert result is None
        
        Path(f.name).unlink(missing_ok=True)
    
    def test_extract_law_id(self, parser):
        """法律ID抽出テスト"""
        law_id = parser._extract_law_id("/path/to/M32HO089.xml")
        assert law_id == "M32HO089"
    
    def test_extract_law_info(self, parser):
        """法律基本情報抽出テスト"""
        # テスト用のXML要素を作成（名前空間付き）
        root = ET.Element("{http://elaws.e-gov.go.jp/XMLSchema}law")
        title_elem = ET.SubElement(root, "{http://elaws.e-gov.go.jp/XMLSchema}LawTitle")
        title_elem.text = "所得税法"
        
        kana_elem = ET.SubElement(root, "{http://elaws.e-gov.go.jp/XMLSchema}LawTitleKana")
        kana_elem.text = "しょとくぜいほう"
        
        num_elem = ET.SubElement(root, "{http://elaws.e-gov.go.jp/XMLSchema}LawNum")
        num_elem.text = "昭和32年法律第89号"
        
        law_info = parser._extract_law_info(root, "M32HO089")
        
        assert law_info["law_name"] == "所得税法"
        assert law_info["law_name_kana"] == "しょとくぜいほう"
        assert law_info["law_number"] == "昭和32年法律第89号"
        assert law_info["category"] == "税法"
    
    def test_extract_articles(self, parser):
        """条文抽出テスト"""
        # テスト用のXML要素を作成（名前空間付き）
        root = ET.Element("{http://elaws.e-gov.go.jp/XMLSchema}law")
        article1 = ET.SubElement(root, "{http://elaws.e-gov.go.jp/XMLSchema}Article")
        num1 = ET.SubElement(article1, "{http://elaws.e-gov.go.jp/XMLSchema}ArticleNum")
        num1.text = "第1条"
        caption1 = ET.SubElement(article1, "{http://elaws.e-gov.go.jp/XMLSchema}ArticleCaption")
        caption1.text = "この法律は、個人の所得に係る税金について定める。"
        
        article2 = ET.SubElement(root, "{http://elaws.e-gov.go.jp/XMLSchema}Article")
        num2 = ET.SubElement(article2, "{http://elaws.e-gov.go.jp/XMLSchema}ArticleNum")
        num2.text = "第2条"
        caption2 = ET.SubElement(article2, "{http://elaws.e-gov.go.jp/XMLSchema}ArticleCaption")
        caption2.text = "所得とは、個人の収入から必要経費を差し引いた金額をいう。"
        
        articles = parser._extract_articles(root, "M32HO089")
        
        assert len(articles) == 2
        assert articles[0].article_number == "第1条"
        assert articles[0].content == "この法律は、個人の所得に係る税金について定める。"
        assert articles[1].article_number == "第2条"
        assert articles[1].content == "所得とは、個人の収入から必要経費を差し引いた金額をいう。"
    
    def test_clean_text(self, parser):
        """テキストクリーニングテスト"""
        # 改行・タブの正規化
        text = "これは\tテスト\nです。"
        cleaned = parser._clean_text(text)
        assert cleaned == "これは テスト です。"
        
        # 前後の空白削除
        text = "  テスト  "
        cleaned = parser._clean_text(text)
        assert cleaned == "テスト"
        
        # 全角スペースの処理
        text = "これは　テストです"
        cleaned = parser._clean_text(text)
        assert cleaned == "これは テストです"
        
        # 空文字列
        cleaned = parser._clean_text("")
        assert cleaned == ""
        
        # None
        cleaned = parser._clean_text(None)
        assert cleaned == ""


class TestDataPreprocessor:
    """DataPreprocessorのテストクラス"""
    
    @pytest.fixture
    def preprocessor(self):
        """データ前処理器のフィクスチャ"""
        return DataPreprocessor()
    
    @pytest.fixture
    def sample_law_document(self):
        """サンプル法律文書のフィクスチャ"""
        articles = [
            Article(
                law_id="M32HO089",
                article_number="第1条",
                content="この法律は、個人の所得に係る税金について定める。",
                metadata={"original": "test"}
            ),
            Article(
                law_id="M32HO089",
                article_number="第2条",
                content="所得とは、個人の収入から必要経費を差し引いた金額をいう。",
                metadata={"original": "test"}
            )
        ]
        
        return LawDocument(
            law_id="M32HO089",
            law_name="所得税法",
            law_name_kana="しょとくぜいほう",
            law_number="昭和32年法律第89号",
            promulgation_date="1957-03-31",
            effective_date="1957-04-01",
            category="税法",
            description="個人の所得に係る税金について定める法律",
            articles=articles
        )
    
    def test_init(self, preprocessor):
        """初期化テスト"""
        assert preprocessor is not None
        assert preprocessor.parser is not None
    
    def test_process_law_document(self, preprocessor, sample_law_document):
        """法律文書前処理テスト"""
        result = preprocessor.process_law_document(sample_law_document)
        
        assert result is not None
        assert isinstance(result, LawDocument)
        assert result.law_id == sample_law_document.law_id
        assert result.law_name == sample_law_document.law_name
        assert len(result.articles) == len(sample_law_document.articles)
        
        # 条文の前処理確認
        for i, article in enumerate(result.articles):
            assert article.law_id == sample_law_document.articles[i].law_id
            assert article.article_number == sample_law_document.articles[i].article_number
            assert article.content == sample_law_document.articles[i].content
            assert article.metadata is not None
            assert "content_length" in article.metadata
            assert "word_count" in article.metadata
            assert "processed_at" in article.metadata
    
    def test_process_article(self, preprocessor):
        """条文前処理テスト"""
        article = Article(
            law_id="M32HO089",
            article_number="第1条",
            content="この法律は、個人の所得に係る税金について定める。",
            metadata={"original": "test"}
        )
        
        result = preprocessor._process_article(article)
        
        assert result is not None
        assert result.law_id == article.law_id
        assert result.article_number == article.article_number
        assert result.content == article.content
        assert result.metadata is not None
        assert result.metadata["content_length"] == len(article.content)
        assert result.metadata["word_count"] == len(article.content.split())
        assert "processed_at" in result.metadata
    
    def test_process_article_empty_content(self, preprocessor):
        """空内容の条文前処理テスト"""
        article = Article(
            law_id="M32HO089",
            article_number="第1条",
            content="",
            metadata={"original": "test"}
        )
        
        result = preprocessor._process_article(article)
        
        assert result is None
    
    def test_clean_article_content(self, preprocessor):
        """条文内容クリーニングテスト"""
        # 基本的なクリーニング
        content = "これは\tテスト\nです。"
        cleaned = preprocessor._clean_article_content(content)
        assert cleaned == "これは テスト です。"
        
        # 前後の空白削除
        content = "  テスト  "
        cleaned = preprocessor._clean_article_content(content)
        assert cleaned == "テスト"
        
        # 全角スペースの処理
        content = "これは　テストです"
        cleaned = preprocessor._clean_article_content(content)
        assert cleaned == "これは テストです"
        
        # 空文字列
        cleaned = preprocessor._clean_article_content("")
        assert cleaned == ""
        
        # None
        cleaned = preprocessor._clean_article_content(None)
        assert cleaned == ""
    
    def test_split_long_article(self, preprocessor):
        """長い条文分割テスト"""
        # 短い条文（分割不要）
        short_article = Article(
            law_id="M32HO089",
            article_number="第1条",
            content="短い条文です。",
            metadata={"original": "test"}
        )
        
        result = preprocessor.split_long_article(short_article, max_length=1000)
        assert len(result) == 1
        assert result[0].article_number == "第1条"
        
        # 長い条文（分割必要）
        long_content = "。".join(["長い条文の文" for _ in range(200)]) + "。"
        long_article = Article(
            law_id="M32HO089",
            article_number="第1条",
            content=long_content,
            metadata={"original": "test"}
        )
        
        result = preprocessor.split_long_article(long_article, max_length=100)
        assert len(result) > 1
        
        # 分割された条文の確認
        for i, split_article in enumerate(result):
            assert split_article.law_id == long_article.law_id
            assert split_article.article_number == f"第1条-{i+1}"
            assert len(split_article.content) <= 100
            assert split_article.metadata["split_from"] == "第1条"
            assert split_article.metadata["split_index"] == i + 1
