from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from datetime import date, timedelta
import io
import os

# Basic function for drawing text on the PDF
def draw_text(c, text: str, x_pos: int, y_pos: int, font_size:int):
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x_pos, y_pos, text)

# Function for drawing contact info
def draw_contact_info(c, x_pos, starting_y_pos, font_size, attribs):
    offset = 18
    for i in attribs:
        i = i if i else ""
        draw_text(c, i, x_pos, starting_y_pos, font_size)
        starting_y_pos -= offset
        
# Draw the info related to base price and additional costs
def draw_costs(c, x_pos, starting_y_pos, font_size, attribs):
    subtotal = attribs[0]
    tax_rate = attribs[1]
    tax = "Unknown" if tax_rate == "Unknown" else subtotal * (tax_rate/100)
    shipping = attribs[2] if attribs[2] else "Unknown"
    discount = attribs[3] if attribs[3] else "None"
    total = subtotal
    total = total + tax if tax != "Unknown" else total
    total = total + shipping if shipping != "Unknown" else total
    total = total - discount if discount != "None" else total
    
    draw_text(c, str(subtotal), x_pos, starting_y_pos, font_size)
    y_pos = starting_y_pos - 37
    offset = 18
    for i in [tax_rate, tax, shipping, discount, total]:
        draw_text(c, str(i), x_pos, y_pos, font_size)
        y_pos -= offset

    # Hit external API to get sales tax based on zip code
    # A lot of the listing zip code fields are empty so this data will be unknown in the invoice
    # A good listing with a zip code : https://www.withgarage.com/listing/15045d96-b358-4109-aa43-2bde7e9ca49c
def get_sales_tax(zip:str):
    get_url = "https://api.api-ninjas.com/v1/salestax?zip_code=" + zip
    headers={"X-Api-Key":os.getenv('TAX_API_KEY')}
    try:
        tax_info = requests.get(get_url, headers=headers)
        return "Unknown" if isinstance(tax_info.json(), dict) else tax_info.json()[0]['total_rate']
    except HTTPError as http_err:
        print(f"HTTP error occurred during sales tax API call: {http_err}")
    except Timeout as timeout_err:
        print(f"Timeout error occurred during sales tax API call: {timeout_err}")
    except RequestException as req_err:
        print(f"Request error occurred during sales tax API call: {req_err}")
    except ValueError as json_err:
        print(f"JSON decoding error during sales tax API call: {json_err}")
    except Exception as err:
        print(f"An error occurred during sales tax API call: {err}")

# Function to draw the current date and payment due date
def draw_dates(c, x_pos, startng_y_pos, font_size):
    curr_date = date.today()
    due_date = curr_date + timedelta(days=30)
    draw_text(c, str(curr_date), x_pos, startng_y_pos, font_size)
    draw_text(c, str(due_date), x_pos, startng_y_pos-70, font_size)

# Function to draw info related to the item itself (name, description) in center of invoice  
def draw_item(c, starting_x_pos, y_pos, font_size, attribs):
    title_text = c.beginText(starting_x_pos, y_pos)
    title_text.setFont("Helvetica-Bold", font_size)
    for word in attribs[0].split(" "):
        if(len(word) > 7) :
            title_text.textLine(word[:7] + '-')
            title_text.textLine(word[7:])
        else:
            title_text.textLine(word)
    c.drawText(title_text)
    
    x_pos = starting_x_pos + 40
    desc_text = c.beginText(x_pos, y_pos)
    desc_text.setFont("Helvetica-Bold", font_size)
    wrapped_lines = wrap_text(attribs[1].replace("\n", " // "), 63)
    for line in wrapped_lines:
        desc_text.textLine(line)
    c.drawText(desc_text)
    offsets = [320, 40, 90]
    for idx, i in enumerate(attribs[2:]):
        i = i if i else ""
        x_pos += offsets[idx]
        draw_text(c, str(i), x_pos, y_pos, font_size)
        
# Wrap the description text so it stays in the box
def wrap_text(text, line_length):
    words = text.split()
    lines = []
    curr_lines = []
    running = 0
    for word in words:
        running+= len(word)
        if running > line_length:
            lines.append(" ".join(curr_lines))
            curr_lines = [word]
            running = len(word)
        else:
            curr_lines.append(word)
    lines.append(" ".join(curr_lines))
    return lines

# Central engine of the pdf creation
def update_pdf(input_pdf: str, data_dict: dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    contact_attribs = [data_dict.get('name'), data_dict.get('company'), data_dict.get('address1'), data_dict.get('address2'), data_dict.get('phone')]
    draw_contact_info(c, 125, 640, 9, contact_attribs)
    draw_contact_info(c, 475, 640, 9, contact_attribs)
    
    item_attribs = [data_dict.get('listingTitle'), data_dict.get('listingDescription'), "1", data_dict.get('sellingPrice'), data_dict.get('sellingPrice')]
    draw_item(c, 25, 530, 8, item_attribs)
    
    zip_code = data_dict.get('addressZip')
    print(zip_code)
    sales_tax = get_sales_tax(data_dict.get('addressZip'))
    sales_tax = sales_tax if sales_tax == "Unknown" else float(sales_tax) * 100
    cost_attribs = [data_dict.get('sellingPrice'), sales_tax, data_dict.get('shippingPrice'), data_dict.get('discount')]
    draw_costs(c, 510, 263, 10, cost_attribs)
    
    draw_dates(c, 480, 750, 9)
    c.save()
    buffer.seek(0)
    
    template = PdfReader(input_pdf)
    overlay = PdfReader(buffer)
    output_buffer = io.BytesIO()
    for pg_num, pg in enumerate(template.pages):
        overlay_pg = overlay.pages[pg_num]
        merged = PageMerge(page=pg)
        merged.add(overlay_pg).render()
    PdfWriter(output_buffer, trailer=template).write()
    output_buffer.seek(0)
    
    return output_buffer
