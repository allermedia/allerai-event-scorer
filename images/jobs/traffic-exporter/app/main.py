
from datetime import datetime, timezone, timedelta
import os
from data_access import DataAccess
from platform_service import PlatformService

if __name__ == "__main__":
    project_id = os.environ.get('ADP_PROJECT_ID', 'aller-data-platform-prod-1f89')
    data_access = DataAccess(project_id)
    platform_service = PlatformService()

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()

    pageviews = data_access.get_pageviews(
        event_date = yesterday
    )

    pages = data_access.get_cms_ids()

    final_rows = []

    for row in pageviews:
        final_rows.append({
            "event_date": row.event_date,
            "page_id": row.page_id,
            "cms_page_id": pages.get(row.page_id),
            "market": row.market,
            "site_domain": row.site_domain,
            "sessions": row.sessions,
            "pageviews": row.pageviews
        })
    
    #Transform row to schema (to be defined)

    #post to platform

    #platform_service.post_article_traffic_to_platform(
    #    data = final_rows,
    #    url = "https://article-gateway.ai.aller.com/api/v1/pageviews"
    #)
