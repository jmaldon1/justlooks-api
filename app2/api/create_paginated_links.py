from urllib.parse import urlparse, urlsplit, urlunparse


def create_header_links(request_url, per_page, current_page, total_records):
    links = []

    # url = PaginatedResponse.__get_url_without_pagination()
    total_pages = ((total_records - 1) // per_page) + 1

    if not is_first_page(current_page):
        links.append(create_link(request_url, per_page, 1, 'first'))

    if not is_last_page(per_page, current_page, total_records) and total_pages is not 0:
        links.append(create_link(request_url, per_page, total_pages, 'last'))

    if has_next(per_page, current_page, total_records):
        links.append(create_link(request_url, per_page, current_page + 1, 'next'))

    if has_previous(current_page, total_records) and total_pages is not 0:
        previous_page = min(current_page - 1, total_records / per_page)
        links.append(create_link(request_url, per_page, previous_page, 'prev'))

    return {
        "Link": ', '.join(links)
    }


def is_first_page(current_page):
    return current_page == 1


def is_last_page(per_page, current_page, total):
    return per_page * current_page >= total > per_page * (current_page - 1)


def has_next(per_page, current_page, total):
    return current_page * per_page < total


def has_previous(current_page, total):
    return current_page > 1


def create_link(request_url: str, per_page: int, page: int, rel: str) -> str:
    r1 = urlparse(request_url)
    updated_queries_template = f"per_page={per_page}&page={page}"
    r2 = r1._replace(query=updated_queries_template)
    next_url = urlunparse(r2)
    link_header_template = f'<{next_url}>; rel="{rel}"'

    return link_header_template
