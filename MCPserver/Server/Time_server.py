from mcp.server.fastmcp import FastMCP
from tzlocal import get_localzone_name
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import sys, datetime

mcp = FastMCP("mcp_adk_Time")

def detect_timezone(default_timezone="Asia/Taipei") -> str:
    try:
        tz_name = get_localzone_name()
        ZoneInfo(tz_name)
        print(f"Detect local time zone:{tz_name}")
        return tz_name
    except Exception as e:
        print(f"Failed to detect time zone:{e}, use presets instead {default_timezone}")
        return default_timezone

local_timezone_name = detect_timezone()

@mcp.tool("get_current_time")
def get_current_time() -> str:
    """Get the current local time."""
    tz = ZoneInfo(local_timezone_name)
    now = datetime.datetime.now(tz)
    return now.isoformat()

# 主程式
if __name__ == "__main__":
    mcp.run(transport="stdio")
