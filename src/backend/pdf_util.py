from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pdfrw import PdfReader, PdfWriter, PageMerge
import requests
from requests.exceptions import HTTPError, Timeout, RequestException
from datetime import date, timedelta
import io
import os

input_pdf = 'sales-invoice.pdf'
output_pdf = 'completed-sales-invoice.pdf'

def draw_text(c, text: str, x_pos: int, y_pos: int, font_size:int):
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x_pos, y_pos, text)

def draw_contact_info(c, x_pos, starting_y_pos, font_size, attribs):
    offset = 18
    for i in attribs:
        i = i if i else ""
        draw_text(c, i, x_pos, starting_y_pos, font_size)
        starting_y_pos -= offset
        
        
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

def draw_dates(c, x_pos, startng_y_pos, font_size):
    curr_date = date.today()
    due_date = curr_date + timedelta(days=30)
    draw_text(c, str(curr_date), x_pos, startng_y_pos, font_size)
    draw_text(c, str(due_date), x_pos, startng_y_pos-70, font_size)
    
def draw_item(c, starting_x_pos, y_pos, font_size, attribs):
    title_text = c.beginText(starting_x_pos, y_pos)
    title_text.setFont("Helvetica-Bold", font_size)
    for word in attribs[0].split(" "):
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
       
def update_pdf(input_pdf: str, output_pdf: str, data_dict: dict):
    # temp_pdf = 'temp.pdf'
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    contact_attribs = [data_dict.get('name'), data_dict.get('company'), data_dict.get('address1'), data_dict.get('address2'), data_dict.get('phone')]
    draw_contact_info(c, 125, 640, 9, contact_attribs)
    draw_contact_info(c, 475, 640, 9, contact_attribs)
    
    item_attribs = [data_dict.get('listingTitle'), data_dict.get('listingDescription'), "1", data_dict.get('sellingPrice'), data_dict.get('sellingPrice')]
    draw_item(c, 25, 530, 8, item_attribs)
    
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

info = {'Name':'John Peterson', 'Company':'The Fire House', 'Address1':'12 Dewberry Street', 'Phone':'918-785-0983', 'addressZip':'10001', 'sellingPrice':10000, 'listingTitle': "2008 Pierce Impel Top Mount Pump", 'listingDescription':'This 2008 Pierce Impel has seating for 6 (5 SCBA), a 1,500 gpm Waterous pump, 750 gallon tank, foam system, Harrison 6.0kW generator and hydraulic ladder rack.   LED lightbar, warning lights and rear rotators, and special SCBA storage for 7 bottles in the R1 compartment.   \n\nBasic Info\n\nManufacturer: Pierce\nModel: Impel XM\nTruck Type: Pumper\nYear: 2008\n\nChassis Info\n\nMake: Pierce\nMileage: 114152\nPower Steering: Y \nWheelbase: 218\"\nLength: 34\'6\"\nAll Wheel Drive: N\nAxles: 2\nHeight: 9/11\" \nWidth: 9: 9\'\n\nEngine Info\n\nMake: Cummins\nTurbo: Yes\nBattery: 6\nFuel: Diesel\nHours: 10415\n\nCab Info\n\nMaterial: Aluminum \nSeating: 6\nAir Conditioning: Y\nSeating Type: 5 SCBA\n\nPump Info\n\nMake: Waterous\nGPM: 1500\nLocation: Top Mount\nPump & Roll: N\nDeck Gun: Y\nBooster Reels: No\nDump Value: No\nModel: CSU\nStages: 1\nTest Date\" 2/4/24\nDischarges: 4\nCrosslays: 2 speedlays (1.75\")\nIntake suction: Yes, 2\n\nTank Info\n\nSize in Gallon: 750\nMaterial: Poly\n\nTransmission Info\n\nMake: Allison\nType: Auto\nModel: 3000\nBrake: Jake\n\nBody Info\n\nMake: Aluminum \nCompartment Door Type: Roll up, painted\nCompartment door #: 7\n\nFoam Info\n\nMake: Husky\nMaterial: Poly\nTank Size: 30\n\n'}
# update_pdf(input_pdf=input_pdf, output_pdf=output_pdf, data_dict=info)
