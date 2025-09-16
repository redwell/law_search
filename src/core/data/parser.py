"""
XMLパーサーとデータ前処理モジュール
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """条文データクラス"""
    law_id: str
    article_number: str
    content: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    paragraph: Optional[str] = None
    effective_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LawDocument:
    """法律文書データクラス"""
    law_id: str
    law_name: str
    law_name_kana: Optional[str] = None
    law_number: Optional[str] = None
    promulgation_date: Optional[str] = None
    effective_date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    articles: List[Article] = None
    
    def __post_init__(self):
        if self.articles is None:
            self.articles = []


class XMLParser:
    """XMLパーサークラス"""
    
    def __init__(self):
        """初期化"""
        self.namespaces = {
            'law': 'http://elaws.e-gov.go.jp/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def parse_law_xml(self, xml_file_path: str) -> Optional[LawDocument]:
        """
        法律XMLファイルをパース
        
        Args:
            xml_file_path: XMLファイルのパス
            
        Returns:
            法律文書データ
        """
        try:
            logger.info(f"XMLファイルをパース中: {xml_file_path}")
            
            # XMLファイルの読み込み
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # 法律IDの取得
            law_id = self._extract_law_id(xml_file_path)
            
            # 法律基本情報の抽出
            law_info = self._extract_law_info(root, law_id)
            
            # 条文の抽出
            articles = self._extract_articles(root, law_id)
            
            # 法律文書の作成
            law_document = LawDocument(
                law_id=law_id,
                law_name=law_info.get("law_name", ""),
                law_name_kana=law_info.get("law_name_kana"),
                law_number=law_info.get("law_number"),
                promulgation_date=law_info.get("promulgation_date"),
                effective_date=law_info.get("effective_date"),
                category=law_info.get("category"),
                description=law_info.get("description"),
                articles=articles
            )
            
            logger.info(f"パース完了: {law_id}, 条文数: {len(articles)}")
            return law_document
            
        except ET.ParseError as e:
            logger.error(f"XMLパースエラー: {xml_file_path}, {str(e)}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {xml_file_path}, {str(e)}")
            return None
    
    def _extract_law_id(self, xml_file_path: str) -> str:
        """
        法律IDを抽出
        
        Args:
            xml_file_path: XMLファイルのパス
            
        Returns:
            法律ID
        """
        return Path(xml_file_path).stem
    
    def _extract_law_info(self, root: ET.Element, law_id: str) -> Dict[str, Any]:
        """
        法律基本情報を抽出
        
        Args:
            root: XMLルート要素
            law_id: 法律ID
            
        Returns:
            法律基本情報
        """
        law_info = {}
        
        try:
            # 法律名の抽出
            law_name_elem = root.find('.//law:LawTitle', self.namespaces)
            if law_name_elem is not None:
                law_info["law_name"] = law_name_elem.text.strip()
            
            # 法律名（カナ）の抽出
            law_name_kana_elem = root.find('.//law:LawTitleKana', self.namespaces)
            if law_name_kana_elem is not None:
                law_info["law_name_kana"] = law_name_kana_elem.text.strip()
            
            # 法律番号の抽出
            law_number_elem = root.find('.//law:LawNum', self.namespaces)
            if law_number_elem is not None:
                law_info["law_number"] = law_number_elem.text.strip()
            
            # 公布日の抽出
            promulgation_date_elem = root.find('.//law:PromulgateDate', self.namespaces)
            if promulgation_date_elem is not None:
                law_info["promulgation_date"] = promulgation_date_elem.text.strip()
            
            # 施行日の抽出
            effective_date_elem = root.find('.//law:EffectiveDate', self.namespaces)
            if effective_date_elem is not None:
                law_info["effective_date"] = effective_date_elem.text.strip()
            
            # カテゴリの推定（法律名から）
            law_name = law_info.get("law_name", "")
            if "税" in law_name:
                law_info["category"] = "税法"
            elif "民法" in law_name:
                law_info["category"] = "民法"
            elif "刑法" in law_name:
                law_info["category"] = "刑法"
            elif "商法" in law_name:
                law_info["category"] = "商法"
            elif "労働" in law_name:
                law_info["category"] = "労働法"
            else:
                law_info["category"] = "その他"
            
            # 説明の生成
            law_info["description"] = f"{law_info.get('law_name', '')}に関する法律"
            
        except Exception as e:
            logger.warning(f"法律基本情報の抽出でエラー: {law_id}, {str(e)}")
        
        return law_info
    
    def _extract_articles(self, root: ET.Element, law_id: str) -> List[Article]:
        """
        条文を抽出
        
        Args:
            root: XMLルート要素
            law_id: 法律ID
            
        Returns:
            条文のリスト
        """
        articles = []
        
        try:
            # 条文要素の検索
            article_elements = root.findall('.//law:Article', self.namespaces)
            
            for article_elem in article_elements:
                article = self._parse_article_element(article_elem, law_id)
                if article:
                    articles.append(article)
            
            # 条項要素の検索（Article要素がない場合）
            if not articles:
                item_elements = root.findall('.//law:Item', self.namespaces)
                for item_elem in item_elements:
                    article = self._parse_item_element(item_elem, law_id)
                    if article:
                        articles.append(article)
            
        except Exception as e:
            logger.warning(f"条文抽出でエラー: {law_id}, {str(e)}")
        
        return articles
    
    def _parse_article_element(self, article_elem: ET.Element, law_id: str) -> Optional[Article]:
        """
        条文要素をパース
        
        Args:
            article_elem: 条文要素
            law_id: 法律ID
            
        Returns:
            条文データ
        """
        try:
            # 条番号の抽出
            article_number = self._extract_article_number(article_elem)
            if not article_number:
                return None
            
            # 条文内容の抽出
            content = self._extract_article_content(article_elem)
            if not content:
                return None
            
            # 章・節・款の抽出
            chapter, section, subsection = self._extract_structure_info(article_elem)
            
            # 条文データの作成
            article = Article(
                law_id=law_id,
                article_number=article_number,
                content=content,
                chapter=chapter,
                section=section,
                subsection=subsection,
                metadata={
                    "xml_element": "Article",
                    "parsed_at": datetime.now().isoformat()
                }
            )
            
            return article
            
        except Exception as e:
            logger.warning(f"条文要素のパースでエラー: {str(e)}")
            return None
    
    def _parse_item_element(self, item_elem: ET.Element, law_id: str) -> Optional[Article]:
        """
        条項要素をパース
        
        Args:
            item_elem: 条項要素
            law_id: 法律ID
            
        Returns:
            条文データ
        """
        try:
            # 条項番号の抽出
            item_number = self._extract_item_number(item_elem)
            if not item_number:
                return None
            
            # 条項内容の抽出
            content = self._extract_item_content(item_elem)
            if not content:
                return None
            
            # 条文データの作成
            article = Article(
                law_id=law_id,
                article_number=item_number,
                content=content,
                metadata={
                    "xml_element": "Item",
                    "parsed_at": datetime.now().isoformat()
                }
            )
            
            return article
            
        except Exception as e:
            logger.warning(f"条項要素のパースでエラー: {str(e)}")
            return None
    
    def _extract_article_number(self, article_elem: ET.Element) -> Optional[str]:
        """条番号を抽出"""
        # 条番号要素の検索
        number_elem = article_elem.find('law:ArticleNum', self.namespaces)
        if number_elem is not None and number_elem.text:
            return number_elem.text.strip()
        
        # 属性から条番号を取得
        if 'Num' in article_elem.attrib:
            return article_elem.attrib['Num']
        
        return None
    
    def _extract_article_content(self, article_elem: ET.Element) -> Optional[str]:
        """条文内容を抽出"""
        # 条文内容要素の検索
        content_elem = article_elem.find('law:ArticleCaption', self.namespaces)
        if content_elem is not None and content_elem.text:
            return self._clean_text(content_elem.text)
        
        # 条項内容の検索
        item_elem = article_elem.find('law:Item', self.namespaces)
        if item_elem is not None and item_elem.text:
            return self._clean_text(item_elem.text)
        
        # 直接のテキスト内容
        if article_elem.text:
            return self._clean_text(article_elem.text)
        
        return None
    
    def _extract_item_number(self, item_elem: ET.Element) -> Optional[str]:
        """条項番号を抽出"""
        # 条項番号要素の検索
        number_elem = item_elem.find('law:ItemNum', self.namespaces)
        if number_elem is not None and number_elem.text:
            return number_elem.text.strip()
        
        # 属性から条項番号を取得
        if 'Num' in item_elem.attrib:
            return item_elem.attrib['Num']
        
        return None
    
    def _extract_item_content(self, item_elem: ET.Element) -> Optional[str]:
        """条項内容を抽出"""
        # 条項内容要素の検索
        content_elem = item_elem.find('law:ItemCaption', self.namespaces)
        if content_elem is not None and content_elem.text:
            return self._clean_text(content_elem.text)
        
        # 直接のテキスト内容
        if item_elem.text:
            return self._clean_text(item_elem.text)
        
        return None
    
    def _extract_structure_info(self, article_elem: ET.Element) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """章・節・款の情報を抽出"""
        chapter = None
        section = None
        subsection = None
        
        try:
            # 親要素から構造情報を取得
            # ElementTreeではgetparent()が使えないため、別の方法で実装
            # 現在は簡易実装としてNoneを返す
            pass
        except Exception as e:
            logger.warning(f"構造情報の抽出でエラー: {str(e)}")
        
        return chapter, section, subsection
    
    def _extract_text_from_element(self, elem: ET.Element) -> Optional[str]:
        """要素からテキストを抽出"""
        if elem.text:
            return self._clean_text(elem.text)
        
        # 子要素からテキストを取得
        for child in elem:
            if child.text:
                return self._clean_text(child.text)
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        テキストをクリーニング
        
        Args:
            text: 元のテキスト
            
        Returns:
            クリーニングされたテキスト
        """
        if not text:
            return ""
        
        # 改行・タブの正規化
        text = re.sub(r'\s+', ' ', text)
        
        # 前後の空白を削除
        text = text.strip()
        
        # 特殊文字の処理
        text = text.replace('\u3000', ' ')  # 全角スペースを半角に
        
        return text


class DataPreprocessor:
    """データ前処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.parser = XMLParser()
    
    def process_law_document(self, law_document: LawDocument) -> LawDocument:
        """
        法律文書を前処理
        
        Args:
            law_document: 法律文書
            
        Returns:
            前処理された法律文書
        """
        logger.info(f"法律文書の前処理を開始: {law_document.law_id}")
        
        # 条文の前処理
        processed_articles = []
        for article in law_document.articles:
            processed_article = self._process_article(article)
            if processed_article:
                processed_articles.append(processed_article)
        
        # 前処理された法律文書の作成
        processed_document = LawDocument(
            law_id=law_document.law_id,
            law_name=law_document.law_name,
            law_name_kana=law_document.law_name_kana,
            law_number=law_document.law_number,
            promulgation_date=law_document.promulgation_date,
            effective_date=law_document.effective_date,
            category=law_document.category,
            description=law_document.description,
            articles=processed_articles
        )
        
        logger.info(f"前処理完了: {law_document.law_id}, 条文数: {len(processed_articles)}")
        return processed_document
    
    def _process_article(self, article: Article) -> Optional[Article]:
        """
        条文を前処理
        
        Args:
            article: 条文
            
        Returns:
            前処理された条文
        """
        try:
            # 内容のクリーニング
            cleaned_content = self._clean_article_content(article.content)
            if not cleaned_content:
                return None
            
            # メタデータの更新
            metadata = article.metadata or {}
            metadata.update({
                "content_length": len(cleaned_content),
                "word_count": len(cleaned_content.split()),
                "processed_at": datetime.now().isoformat()
            })
            
            # 前処理された条文の作成
            processed_article = Article(
                law_id=article.law_id,
                article_number=article.article_number,
                content=cleaned_content,
                chapter=article.chapter,
                section=article.section,
                subsection=article.subsection,
                paragraph=article.paragraph,
                effective_date=article.effective_date,
                metadata=metadata
            )
            
            return processed_article
            
        except Exception as e:
            logger.warning(f"条文の前処理でエラー: {article.law_id}-{article.article_number}, {str(e)}")
            return None
    
    def _clean_article_content(self, content: str) -> str:
        """
        条文内容をクリーニング
        
        Args:
            content: 元の内容
            
        Returns:
            クリーニングされた内容
        """
        if not content:
            return ""
        
        # 基本的なクリーニング
        content = re.sub(r'\s+', ' ', content)  # 連続する空白を単一の空白に
        content = content.strip()  # 前後の空白を削除
        
        # 不要な文字の削除
        content = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F]', '', content)
        
        # 全角スペースを半角に
        content = content.replace('\u3000', ' ')
        
        # 連続する空白を単一に
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def split_long_article(self, article: Article, max_length: int = 1000) -> List[Article]:
        """
        長い条文を分割
        
        Args:
            article: 条文
            max_length: 最大長
            
        Returns:
            分割された条文のリスト
        """
        if len(article.content) <= max_length:
            return [article]
        
        # 文単位で分割
        sentences = re.split(r'[。！？]', article.content)
        
        split_articles = []
        current_content = ""
        current_index = 1
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # 現在の内容に文を追加した場合の長さをチェック
            test_content = current_content + sentence + "。"
            
            if len(test_content) > max_length and current_content:
                # 現在の内容で条文を作成
                split_article = Article(
                    law_id=article.law_id,
                    article_number=f"{article.article_number}-{current_index}",
                    content=current_content.strip(),
                    chapter=article.chapter,
                    section=article.section,
                    subsection=article.subsection,
                    paragraph=article.paragraph,
                    effective_date=article.effective_date,
                    metadata={
                        **(article.metadata or {}),
                        "split_from": article.article_number,
                        "split_index": current_index
                    }
                )
                split_articles.append(split_article)
                
                # 新しい内容を開始
                current_content = sentence + "。"
                current_index += 1
            else:
                current_content = test_content
        
        # 最後の内容を追加
        if current_content:
            split_article = Article(
                law_id=article.law_id,
                article_number=f"{article.article_number}-{current_index}",
                content=current_content.strip(),
                chapter=article.chapter,
                section=article.section,
                subsection=article.subsection,
                paragraph=article.paragraph,
                effective_date=article.effective_date,
                metadata={
                    **(article.metadata or {}),
                    "split_from": article.article_number,
                    "split_index": current_index
                }
            )
            split_articles.append(split_article)
        
        return split_articles
