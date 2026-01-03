import logging
from typing import Dict, List
import json
import os
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    """AI服务"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.moonshot.cn/v1"
        
        if not self.api_key:
            logger.warning("未配置OPENAI_API_KEY，AI功能无法使用")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                                      )
            logger.info("AI模型客户端初始化成功")



    async def generate_summary(self, content: str, max_length: int = 500) -> str:
        """AI生成摘要"""

        try:
            
            if not self.client:
                logger.error("AI client 未初始化")
                return self._fallback_summary(content, max_length)


            prompt = f"""
            请为以下文章生成一个简洁的中文摘要，要求：
            1. 长度控制在{max_length}字以内
            2. 保留核心信息和关键观点
            3. 语言流畅自然
            4. 只返回摘要内容，不要其他说明
            
            文章内容：
            {content}
            """

            response = await self.client.chat.completions.create(
                 model="kimi-k2-0711-preview",
                 messages=[{"role": "user", "content": prompt}],
                 temperature=0.7 
                )

            if  response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content.strip()
                logger.info(f"AI生成摘要成功，长度为：{len(text)}")
                return text
            else:
                logger.warning("AI返回结果为空")
                return self._fallback_summary(content, max_length)

        except Exception as e:
            logger.error(f"AI摘要生成失败: {str(e)}")
            return self._fallback_summary(content, max_length)

    async def classify_article(self, title: str, content: str) -> Dict[str, float]:
        """使用AI分类文章内容"""

        try:
            
            if not self.client:
                return self._fallback_classification(title, content)


            prompt = f"""
            请分析以下文章，将其分类到以下类别中，并给出每个类别的置信度（0-1之间）：
            科技、生活、财经、教育、娱乐、体育、其他
            
            请以JSON格式返回，例如：
            {{"科技": 0.8, "生活": 0.2}}
            
            文章标题：{title}
            文章内容：{content}...
            
            只返回JSON格式，不要其他说明。
            """

            response = await self.client.chat.completions.create(
                    model="kimi-k2-0711-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                    )
            if response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content.strip()
                try:
                    categories = json.loads(text)
                    logger.info(f"AI分类成功：{categories}")
                    return categories
                except json.JSONDecodeError:
                    logger.warning(f"AI返回的不是有效的JSON: {text}")
                    return self._parse_classification_text(text)
            else:
                logger.warning("AI返回内容为空")
                return self._fallback_classification(title, content)
        except Exception as e:
            logger.warning(f"AI分类失败：{str(e)}")
            return self._fallback_classification(title, content)

    async def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """使用AI提取关键词"""
        if not self.client:
            return self._fallback_keywords(content, max_keywords)

        try:
            prompt = f"""
            请从以下文章中提取{max_keywords}个最重要的关键词，要求：
            1. 关键词要准确反映文章主题
            2. 每个关键词1-4个字
            3. 按重要性排序
            4. 只返回关键词，用逗号分隔，不要其他说明
            
            文章内容：
            {content}
            """

            response = await self.client.chat.completions.create(
                    model="kimi-k2-0711-preview",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                    )
            if response.choices and response.choices[0].message.content:
                text = response.choices[0].message.content.strip()
                keywords = [kw.strip() for kw in text.split(',') if kw.strip()]

                keywords = [kw for kw in keywords if len(kw) <= 10 and not kw.startswith("请")]
                logger.info(f"AI关键词提取成功: {keywords}")
                return keywords[:max_keywords]
            else:
                logger.warning("AI返回内容为空")
                return self._fallback_keywords(content, max_keywords)
        except Exception as e:
            logger.error(f"AI关键词提取失败: {str(e)}")
            return self._fallback_keywords(content, max_keywords)

    def _fallback_classification(self, title: str, content: str) -> Dict[str, float]:
        """简单分类"""
        try:
            full_text = (title + "" + content).lower()

            categories = {
                "科技": ["技术", "科技", "AI", "人工智能", "编程", "代码", "软件", "硬件", "互联网"],
                "生活": ["生活", "日常", "美食", "旅行", "健康", "运动", "家庭", "情感"],
                "财经": ["经济", "金融", "投资", "股票", "基金", "理财", "创业", "商业"],
                "教育": ["学习", "教育", "培训", "知识", "课程", "考试", "学校"],
                "娱乐": ["电影", "音乐", "游戏", "综艺", "明星", "娱乐", "搞笑"],
                "体育": ["体育", "足球", "篮球", "运动", "比赛", "运动员", "健身"]
                    }
            scores: Dict[str, int] = {}
            total_score = 0

            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword.lower() in full_text)
                if score > 0:
                    scores[category] = score
                    total_score += score

            if total_score == 0:
                return {"其他": 1.0}

            # 归一化
            result: Dict[str, float] = {category: score / total_score for category, score in scores.items()}
            return result   

        except Exception as e:
            logger.error(f"分类失败：{str(e)}")
            return {"其他": 1.0}

    def _fallback_summary(self, content: str, max_length: int) -> str:
        """回退到简单摘要"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            if len(text) <= max_length:
                return text
            
            truncated = text[:max_length]
            last_period = truncated.rfind('。')
            last_exclamation = truncated.rfind('！')
            last_question = truncated.rfind('？')
            
            sentence_end = max(last_period, last_exclamation, last_question)
            
            if sentence_end > max_length * 0.7:
                return truncated[:sentence_end + 1]
            else:
                return truncated + "..."
                
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return ""

    def _parse_classification_text(self, text: str) -> Dict[str, float]:
        """解析分类文本"""
        try:
            # 尝试从文本中提取分类信息
            categories = {}
            if "科技" in text:
                categories["科技"] = 0.8
            if "生活" in text:
                categories["生活"] = 0.6
            if "财经" in text:
                categories["财经"] = 0.7
            if "教育" in text:
                categories["教育"] = 0.6
            if "娱乐" in text:
                categories["娱乐"] = 0.5
            if "体育" in text:
                categories["体育"] = 0.5
            
            if not categories:
                categories["其他"] = 1.0
            
            return categories
        except:
            return {"其他": 1.0}
    def _fallback_keywords(self, content: str, max_keywords: int) -> List[str]:
        """简单关键词提取"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)

            import re
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z]+', text)

            # 过滤停用词
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
            
            # 统计词频
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按频率排序，返回前N个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            logger.error(f"回退关键词提取失败: {str(e)}")
            return []








