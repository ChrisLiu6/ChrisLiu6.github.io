from scholarly import scholarly, ProxyGenerator
import jsonpickle
import json
from datetime import datetime
import os
import sys
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    scholar_id = "VxQGEOcAAAAJ"
    if not scholar_id:
        logger.error("GOOGLE_SCHOLAR_ID environment variable is not set!")
        sys.exit(1)

    logger.info(f"Starting Google Scholar crawler for ID: {scholar_id}")

    # 尝试设置免费代理（可选，如果直接请求被封）
    max_retries = 3
    retry_delay = 30  # 秒

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries}: Searching for author...")

            # 尝试使用免费代理
            if attempt > 1:
                logger.info("Setting up free proxy...")
                try:
                    pg = ProxyGenerator()
                    success = pg.FreeProxies()
                    if success:
                        scholarly.use_proxy(pg)
                        logger.info("Free proxy configured successfully")
                    else:
                        logger.warning("Failed to configure free proxy, continuing without proxy")
                except Exception as proxy_error:
                    logger.warning(f"Proxy setup failed: {proxy_error}, continuing without proxy")

            # 搜索作者
            logger.info("Fetching author by ID...")
            start_time = time.time()
            author: dict = scholarly.search_author_id(scholar_id)
            elapsed = time.time() - start_time
            logger.info(f"Author found in {elapsed:.2f}s: {author.get('name', 'Unknown')}")

            # 填充详细信息
            logger.info("Filling author details (basics, indices, counts, publications)...")
            start_time = time.time()
            scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
            elapsed = time.time() - start_time
            logger.info(f"Author details filled in {elapsed:.2f}s")

            # 处理数据
            name = author['name']
            author['updated'] = str(datetime.now())
            num_publications = len(author.get('publications', []))
            logger.info(f"Author: {name}, Citations: {author.get('citedby', 'N/A')}, Publications: {num_publications}")

            author['publications'] = {v['author_pub_id']:v for v in author['publications']}

            # 保存结果
            logger.info("Saving results...")
            os.makedirs('results', exist_ok=True)

            with open('results/gs_data.json', 'w') as outfile:
                json.dump(author, outfile, ensure_ascii=False)
            logger.info("Saved gs_data.json")

            shieldio_data = {
                "schemaVersion": 1,
                "label": "citations",
                "message": f"{author['citedby']}",
            }
            with open('results/gs_data_shieldsio.json', 'w') as outfile:
                json.dump(shieldio_data, outfile, ensure_ascii=False)
            logger.info("Saved gs_data_shieldsio.json")

            logger.info("Google Scholar data crawling completed successfully!")
            print(json.dumps(author, indent=2))
            return  # 成功，退出

        except Exception as e:
            logger.error(f"Attempt {attempt}/{max_retries} failed: {type(e).__name__}: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                logger.error("All retry attempts exhausted. Exiting with failure.")
                sys.exit(1)

if __name__ == "__main__":
    main()
