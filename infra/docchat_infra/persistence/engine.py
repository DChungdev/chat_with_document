from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Hàm fn_* và truy vấn không tiền tố schema cần search_path (Database_Design_SQL mục 4.1).
SEARCH_PATH_OPTION = "-csearch_path=docchat,public"


def create_engine(url: str, *, pool_size: int = 10, echo: bool = False) -> AsyncEngine:
    """Tạo engine async. Không bật `echo` ở môi trường thật: câu lệnh có thể kèm tham số."""
    return create_async_engine(
        url,
        pool_size=pool_size,
        pool_pre_ping=True,
        echo=echo,
        hide_parameters=True,
        connect_args={"options": SEARCH_PATH_OPTION},
    )
