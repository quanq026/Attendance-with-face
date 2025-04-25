import discord
from discord.ui import Button, View
from discord.ext import commands
from discord import app_commands
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot ID và TOKEN
CHANNEL_ID = #add ur id channel here   Thay bằng CHANNEL_ID của bạn
TOKEN = "add ur bot token here"         # Thay bằng TOKEN của bạn
# Pagination settings
PAGINATION_LIMIT = 5  # Number of items per page

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
os.chdir(BASE_DIR)
if not os.path.exists(DATABASE_DIR):
    logger.error(f"Thư mục database không tồn tại tại: {DATABASE_DIR}")
    sys.exit(1)
sys.path.append(BASE_DIR)

try:
    from utils import (
        get_all_employees,
        get_employee_name,
        get_employee_dob,
        get_attendance_summary,
        has_attended_on_date,
        load_logs_to_dataframe
    )
except ImportError as error:
    logger.error(f"Lỗi import utils: {error}")
    sys.exit(1)

# Hàm rút gọn tên
def shorten_name(name: str, max_length: int = 20) -> str:
    name = name.strip()
    if len(name) <= max_length:
        return name
    parts = name.split()
    if len(parts) == 1:
        return name
    initials = [word[0].upper() + '.' for word in parts[:-1]]
    return ''.join(initials) + parts[-1]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# File watcher
class NewEmployeeFileHandler(FileSystemEventHandler):
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.last_modified_times = {}
        self.processing = False

    async def process_file_change(self, filepath):
        if self.processing:
            return
        self.processing = True
        try:
            mtime = os.path.getmtime(filepath)
            if filepath in self.last_modified_times and self.last_modified_times[filepath] == mtime:
                return
            self.last_modified_times[filepath] = mtime

            channel = self.bot.get_channel(CHANNEL_ID)
            if not channel:
                logger.error("Không tìm thấy kênh Discord")
                return

            with open(filepath, "r", encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]

            if names:
                message = f"👋 Chào mừng nhân viên mới: {', '.join(names)}"
                await channel.send(message)
                logger.info(f"Đã gửi thông báo: {message}")
                open(filepath, 'w', encoding='utf-8').close()
        except Exception as error:
            logger.error(f"Lỗi xử lý file nhân viên mới: {error}")
        finally:
            self.processing = False

    def on_modified(self, event):
        if event.is_directory or os.path.basename(event.src_path) != "new_employees.txt":
            return
        asyncio.run_coroutine_threadsafe(self.process_file_change(event.src_path), self.bot.loop)

async def start_file_watcher():
    new_file = os.path.join(DATABASE_DIR, "new_employees.txt")
    if not os.path.exists(new_file):
        open(new_file, 'w', encoding='utf-8').close()
    observer = Observer()
    handler = NewEmployeeFileHandler(bot)
    observer.schedule(handler, DATABASE_DIR, recursive=False)
    observer.start()
    logger.info(f"Đang theo dõi thư mục: {DATABASE_DIR}")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        observer.stop()
        observer.join()
        
class PaginationButtons(View):
    def __init__(self, page: int, total_items: int, command: str, interaction: discord.Interaction):
        super().__init__()
        self.page = page
        self.total_items = total_items
        self.command = command
        self.interaction = interaction

    @property
    def total_pages(self):
        return (self.total_items + PAGINATION_LIMIT - 1) // PAGINATION_LIMIT  # Calculate total pages

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await interaction.response.defer()
            await self.update_embed()

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages:
            self.page += 1
            await interaction.response.defer()
            await self.update_embed()

    async def update_embed(self):
        employees = get_all_employees()
        start = (self.page - 1) * PAGINATION_LIMIT
        end = start + PAGINATION_LIMIT
        page_employees = employees[start:end]

        embed = discord.Embed(
            title=f"📋 Danh sách nhân viên (Page {self.page}/{self.total_pages})",
            description="\n".join([f"- ID: {eid} - {get_employee_name(eid)}" for eid in page_employees]),
            color=discord.Color.blue()
        )
        await self.interaction.edit_original_response(embed=embed, view=self)


# === Slash commands ===
@bot.event
async def on_ready():
    logger.info(f"Bot đã sẵn sàng: {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Đã đồng bộ {len(synced)} slash commands")
        bot.loop.create_task(check_birthdays())
        bot.loop.create_task(start_file_watcher())
    except Exception as error:
        logger.error(f"Lỗi khi khởi động bot: {error}")


@bot.tree.command(name="employees", description="Xem danh sách nhân viên đã đăng ký.")
async def list_employees(interaction: discord.Interaction):
    employees = get_all_employees()
    if not employees:
        await interaction.response.send_message("Chưa có nhân viên nào.")
        return

    # Pagination View for employee list
    class EmployeePagination(View):
        def __init__(self, page: int, total_items: int, interaction: discord.Interaction):
            super().__init__()
            self.page = page
            self.total_items = total_items
            self.interaction = interaction

        @property
        def total_pages(self):
            return (self.total_items + PAGINATION_LIMIT - 1) // PAGINATION_LIMIT

        @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 1:
                self.page -= 1
                await interaction.response.defer()
                await self.update_embed()

        @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.total_pages:
                self.page += 1
                await interaction.response.defer()
                await self.update_embed()

        async def update_embed(self):
            start = (self.page - 1) * PAGINATION_LIMIT
            end = start + PAGINATION_LIMIT
            page_employees = employees[start:end]

            embed = discord.Embed(
                title=f"📋 Danh sách nhân viên (Page {self.page}/{self.total_pages})",
                description="\n".join([f"- ID: {eid} - {get_employee_name(eid)}" for eid in page_employees]),
                color=discord.Color.blue()
            )
            await self.interaction.edit_original_response(embed=embed, view=self)

    # Send first page of employee list
    view = EmployeePagination(page=1, total_items=len(employees), interaction=interaction)
    embed = discord.Embed(
        title="📋 Danh sách nhân viên (Page 1)",
        description="\n".join([f"- ID: {eid} - {get_employee_name(eid)}" for eid in employees[:PAGINATION_LIMIT]]),
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=view)



@bot.tree.command(name="list_dob", description="Xem danh sách nhân viên kèm ngày sinh.")
async def list_dob(interaction: discord.Interaction):
    emps = get_all_employees()
    if not emps:
        await interaction.response.send_message("Chưa có nhân viên nào.")
        return

    # Pagination class for list_dob
    class DobPagination(View):
        def __init__(self, page: int, total_items: int, interaction: discord.Interaction):
            super().__init__()
            self.page = page
            self.total_items = total_items
            self.interaction = interaction

        @property
        def total_pages(self):
            return (self.total_items + PAGINATION_LIMIT - 1) // PAGINATION_LIMIT

        @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 1:
                self.page -= 1
                await interaction.response.defer()
                await self.update_embed()

        @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.total_pages:
                self.page += 1
                await interaction.response.defer()
                await self.update_embed()

        async def update_embed(self):
            start = (self.page - 1) * PAGINATION_LIMIT
            end = start + PAGINATION_LIMIT
            page_employees = emps[start:end]

            embed = discord.Embed(
                title=f"🎂 Danh sách ngày sinh (Page {self.page}/{self.total_pages})",
                description="\n".join([
                    f"- ID: {eid} - {get_employee_name(eid)}: {get_employee_dob(eid) or 'Chưa có'}"
                    for eid in page_employees
                ]),
                color=discord.Color.gold()
            )
            await self.interaction.edit_original_response(embed=embed, view=self)

    # Send the first page of employee birthdays
    view = DobPagination(page=1, total_items=len(emps), interaction=interaction)
    embed = discord.Embed(
        title="🎂 Danh sách ngày sinh (Page 1)",
        description="\n".join([
            f"- ID: {eid} - {get_employee_name(eid)}: {get_employee_dob(eid) or 'Chưa có'}"
            for eid in emps[:PAGINATION_LIMIT]
        ]),
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="attendance", description="Báo cáo chấm công hôm nay.")
async def attendance(interaction: discord.Interaction):
    summary = get_attendance_summary()
    not_done = [get_employee_name(e) for e in summary['not_attended_list']]
    embed = discord.Embed(
        title="📆 Báo cáo chấm công hôm nay",
        description=f"✅ Đã chấm: {summary['attended_count']}/{summary['total_employees']}",
        color=discord.Color.green()
    )
    embed.add_field(name="❌ Chưa chấm", value=', '.join(not_done) or "Không", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="check", description="Kiểm tra chấm công theo ID hoặc tên.")
@app_commands.describe(identifier="ID (5 số) hoặc tên", date="Ngày (dd/mm) hoặc để trống để kiểm tra hôm nay")
async def check(interaction: discord.Interaction, identifier: str, date: str = None):
    iden = identifier.strip()
    today = datetime.now().date() if date is None else datetime.strptime(date, "%d/%m").date().replace(year=datetime.now().year)
    
    df = load_logs_to_dataframe()
    embed = discord.Embed(
        title=f"📍 Kết quả kiểm tra chấm công - {today.strftime('%d/%m/%Y')}",  # Add today's date to the title
        color=discord.Color.teal()
    )

    # Initialize description as an empty string to avoid NoneType error
    embed.description = ""

    if iden.isdigit() and len(iden) == 5:
        # Check by ID
        name = get_employee_name(iden)
        if not name:
            await interaction.response.send_message(f"Không tìm thấy ID {iden}.")
            return
        rec = df[(df['ID'].str.strip() == iden) & (df['Thời gian'].dt.date == today)]
        dob = get_employee_dob(iden) or "Chưa có"
        status = f"✅ {name} ({iden}) đã chấm công lúc {rec.iloc[0]['Thời gian'].strftime('%H:%M:%S')}" if not rec.empty else f"❌ {name} ({iden}) chưa chấm công."
        embed.description = f"{status}\n🎂 Ngày sinh: {dob}"
        await interaction.response.send_message(embed=embed)
        return

    # Check by name
    found = False
    for eid in get_all_employees():
        name = get_employee_name(eid)
        if iden.lower() in name.lower():
            rec = df[(df['ID'].str.strip() == eid) & (df['Thời gian'].dt.date == today)]
            dob = get_employee_dob(eid) or "Chưa có"
            status = f"✅ {name} ({eid}) đã chấm công lúc {rec.iloc[0]['Thời gian'].strftime('%H:%M:%S')}" if not rec.empty else f"❌ {name} ({eid}) chưa chấm công."
            embed.description += f"\n\n{status}\n🎂 Ngày sinh: {dob}"
            found = True

    if not found:
        await interaction.response.send_message(f"Không tìm thấy nhân viên nào trùng với '{identifier}' vào ngày {today.strftime('%d/%m/%Y')}.")
    else:
        await interaction.response.send_message(embed=embed)



@bot.tree.command(name="attendance_table", description="Bảng thống kê chấm công.")
@app_commands.describe(param="Số ngày (e.g.7) hoặc ngày cụ thể (dd/mm)")
async def attendance_table(interaction: discord.Interaction, param: str = "7"):
    employees = get_all_employees()
    if not employees:
        return await interaction.response.send_message("Chưa có nhân viên nào.")

    # Xử lý ngày
    today = datetime.now().date()
    year = today.year
    if param.isdigit():
        cnt = int(param)
        dates = [today - timedelta(days=i) for i in range(cnt-1, -1, -1)]
    elif re.match(r"^\d{2}/\d{2}$", param):
        dates = [datetime.strptime(f"{param}/{year}", "%d/%m/%Y").date()]
    else:
        return await interaction.response.send_message("Tham số không hợp lệ.")

    # Pagination class
    class AttendanceTablePagination(View):
        def __init__(self, page: int, total_items: int, interaction: discord.Interaction):
            super().__init__()
            self.page = page
            self.total_items = total_items
            self.interaction = interaction

        @property
        def total_pages(self):
            return (self.total_items + PAGINATION_LIMIT - 1) // PAGINATION_LIMIT

        @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.primary)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 1:
                self.page -= 1
                await interaction.response.defer()
                await self.update_embed()

        @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.total_pages:
                self.page += 1
                await interaction.response.defer()
                await self.update_embed()

        async def update_embed(self):
            start = (self.page - 1) * PAGINATION_LIMIT
            end = start + PAGINATION_LIMIT
            employees_page = employees[start:end]

            embed = discord.Embed(
                title=f"📊 Thống kê chấm công (Page {self.page}/{self.total_pages})",
                description=f"Thống kê từ `{dates[0].strftime('%d/%m/%Y')}` đến `{dates[-1].strftime('%d/%m/%Y')}`",
                colour=discord.Colour.blurple(),
                timestamp=datetime.now()
            )

            # Add headers for the dates
            header_line = ' • '.join(f"`{d.strftime('%d-%m')}`" for d in dates)
            embed.add_field(name="📅 Ngày", value=header_line, inline=False)

            # Add employee status for each page
            for eid in employees_page:
                title = f"{shorten_name(get_employee_name(eid))} (ID: {eid})"
                cells = [f"`{d.strftime('%d')}|{'✅' if has_attended_on_date(eid, d.strftime('%d/%m/%Y')) else '❌'}`" for d in dates]
                cell_line = '  '.join(cells)
                embed.add_field(name=title, value=cell_line, inline=False)

            # Footer text
            footer_text = "✅ = Có mặt   ❌ = Vắng mặt"
            embed.set_footer(text=f"{footer_text} | Trang {view.page}/{view.total_pages}")


            await self.interaction.edit_original_response(embed=embed, view=self)

    # Send the first page of the attendance table
    view = AttendanceTablePagination(page=1, total_items=len(employees), interaction=interaction)
    embed = discord.Embed(
        title="📊 Thống kê chấm công",
        description=f"Thống kê từ `{dates[0].strftime('%d/%m/%Y')}` đến `{dates[-1].strftime('%d/%m/%Y')}`",
        colour=discord.Colour.blurple(),
        timestamp=datetime.now()
    )
    header_line = ' • '.join(f"`{d.strftime('%d-%m')}`" for d in dates)
    embed.add_field(name="📅 Ngày", value=header_line, inline=False)

    # Add employees for the first page
    for eid in employees[:PAGINATION_LIMIT]:
        title = f"{shorten_name(get_employee_name(eid))} (ID: {eid})"
        cells = [f"`{d.strftime('%d')}|{'✅' if has_attended_on_date(eid, d.strftime('%d/%m/%Y')) else '❌'}`" for d in dates]
        cell_line = '  '.join(cells)
        embed.add_field(name=title, value=cell_line, inline=False)

    footer_text = "✅ = Có mặt   ❌ = Vắng mặt"
    embed.set_footer(text=f"{footer_text} | Trang {view.page}/{view.total_pages}")



    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="helppls", description="Hiển thị danh sách lệnh.")
async def helppls(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📌 Danh sách lệnh slash",
        description=(
            "🔹 `/employees` — Danh sách nhân viên.\n"
            "🔹 `/list_dob` — Danh sách ngày sinh.\n"
            "🔹 `/attendance` — Báo cáo hôm nay.\n"
            "🔹 `/check` <ID | tên> — Kiểm tra chấm công.\n"
            "🔹 `/attendance_table` <Số ngày | dd/mm> — Bảng chấm công.\n"
            "🔹 `/helppls` — Hiển thị danh sách lệnh."
        ),
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)

async def check_birthdays():
    while True:
        today_str = datetime.now().strftime("%d/%m")
        bdays = [f"{get_employee_name(e)} ({e})" for e in get_all_employees() if (dob := get_employee_dob(e)) and dob[:5] == today_str]
        if bdays:
            ch = bot.get_channel(CHANNEL_ID)
            await ch.send(f"🎂 Chúc mừng sinh nhật: {', '.join(bdays)}!")
        await asyncio.sleep(86400)

async def main():
    try:
        await bot.start(TOKEN)
    except Exception as error:
        logger.error(f"Bot không khởi động được: {error}")
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
