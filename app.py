import streamlit as st
import pandas as pd
import pdfplumber
import re
import base64


def extract_customer_details(text):
    # Your existing code for extracting customer details
    Orders_data = []
    lines = text.splitlines()  # Split text by line breaks
    customer_name = None
    Order_id = None
    order_items = []
    customer_address = ""
    addressFlag = True
    customerPinCode = ""
    customerCity = ""
    customerMobileNumber = None
    shipping_charges = None
    total_quantity = None
    total_price = None

    # Define the pattern to match the mobile number
    pattern = r"MOBILE NO\. : (\d{10})"
    # Use regex to find the mobile number
    match = re.search(pattern, text)
    # Extract the matched mobile number
    if match:
        customerMobileNumber = match.group(1)
        
        # Define pattern to extract shipping charges and total quantity
    shipping_charges_pattern = r"SHIPPING CHARGES Rs\.(\d+\.\d+)"
    total_quantity_pattern = r"TOTAL (\d+) Rs\."
    total_price_pattern = r"TOTAL \d+ Rs\.([\d,]+\.\d{2})"
    
    # Extract shipping charges
    shipping_charges_match = re.search(shipping_charges_pattern, text)
    if shipping_charges_match:
        shipping_charges = shipping_charges_match.group(1)
        

    # Extract total quantity
    total_quantity_match = re.search(total_quantity_pattern, text)
    if total_quantity_match:
        total_quantity = total_quantity_match.group(1)
        
        
    # Extract total price
    total_price_match = re.search(total_price_pattern, text)
    if total_price_match:
        total_price = total_price_match.group(1).replace(",", "")  # Remove comma from price
        

    for line_index, line in enumerate(lines):
        if line.startswith("DELIVER To:"):
            # Extract customer name from the next line
            if len(lines) > lines.index(line) + 1:
                customer_name = lines[line_index + 1].strip()
                customer_name = customer_name.split()[0:2]
                customer_name = ' '.join(customer_name)
        elif line.startswith("ORDER # :"):
            # Extract order ID from the current line
            Order_id = line.split(": ")[-1].strip()  # Split on ": " and get the last part
        elif line.startswith("SKU ITEM QTY PRICE"):
            # Start collecting order items
            start_item_index = lines.index(line) + 1
        elif line.startswith("SHIPPING CHARGES"):
            # Stop collecting order items
            order_items = lines[start_item_index:line_index]
        elif line.endswith("10005"):
            # Add first word of the line to address and set flag
            customerCity = line.split()[0]
            customer_address += customerCity + "\n"
        elif "110005, India" in line:
            # Define the pattern to match the desired substring
            statePinCodepattern = r"(.*?), IN\b"

            # Use regex to find the matching substring
            match = re.search(statePinCodepattern, line)

            # Extract the matched substring
            if match:
                customerPinCode = match.group(1).strip()
                customer_address += "".join(customerPinCode) + "\n"
                customerPinCode = customerPinCode.split(",")[1].strip()
        elif line_index >= 2:
            if line.endswith("Opposite Metr-"):
                # If "24, 1st Floor" is found, split and join address (excluding parts after)
                substring_to_remove = "24, 1st Floor, Pusa Road, Opposite Metr-"
                cleaned_address_line = re.sub(re.escape(substring_to_remove), "", line).strip()
                customer_address += "".join(cleaned_address_line) + "\n"
                if len(lines) > lines.index(line) + 1:
                    newline = lines[line_index + 1]
                    sub = "o Pillar No-102, Pusa Road, Pusa Road A-"
                    clean = re.sub(re.escape(sub), "", newline).strip()
                    customer_address += "".join(clean) + "\n"
                addressFlag = False
            elif addressFlag == True:
                # Include line if it doesn't contain "24, 1st Floor" (avoid extra split)
                customer_address += line.strip() + "\n"

#     print(customer_name)
#     print(Order_id)
#     print(order_items)
#     print(customer_address)
#     print(customerPinCode)
#     print(customerCity)
#     print(customerMobileNumber)
#     print("Total Price:", total_price)
#     print("Total Quantity:", total_quantity)
#     print("Shipping Charges:", shipping_charges)

    extracted_items = []
    prev=""
    length=len(order_items)
    skus = []
    prices = []
    quantities = []

    for item in order_items:
        # Split the item string on spaces
        if item == 'ok':
            continue
        if len(prev) != 0:
            item = prev + " " + item
            prev = ""
        item_parts = item.split()
        length = len(item_parts)
        if length < 4:
            prev = item
            continue
        print(item)
        # Check if there are enough parts to extract information
        if length >= 4:
            # Extract order ID (first word)
            order_id = item_parts[0]
            if order_id =='Gita' and item_parts[1] =='Rhyme':
                order_id = 'Gita Rhyme Book'
            if order_id == 'Gita_colouring&stickerbo':
                order_id = 'Gita_colouring&stickerbook'
            price = item_parts[length - 1]
            quantity = item_parts[length - 2]

            # Append each order item as a separate row
            Orders_data.append([Order_id, customer_name, customer_address, customerPinCode, 
                            customerCity, customerMobileNumber, order_id, price, quantity, 
                            shipping_charges, total_quantity, total_price])
        else:
            print(f"Warning: Skipping invalid item format: {item}")  # Optional: Log invalid items
    return Orders_data

def extract_data_from_pdf(pdf_path):
    # Your existing code for extracting data from PDF
    # Create an empty DataFrame to accumulate data
    data_rows = []  # List to store rows of data
    df = pd.DataFrame(columns=["Order ID", "Customer Name", "Customer Address", "Pin Code", 
                               "City", "Mobile Number", "SKU", "Price", "Quantity", 
                               "Shipping Charges", "Total Quantity", "Total Price"])

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            # Extract data from the left half of the page
            mid_x = page.width / 2
            left_half = page.within_bbox((0, 0, mid_x, page.height))
            left_text = left_half.extract_text()
            CustomerData1 = extract_customer_details(left_text)

            # Extract data from the right half of the page
            right_half = page.within_bbox((mid_x, 0, page.width, page.height))
            right_text = right_half.extract_text()
            CustomerData2 = extract_customer_details(right_text)

            for row in CustomerData1:
                data_rows.append(row)
            for row in CustomerData2:
                data_rows.append(row)

            # Create DataFrame from the list of data rows
            df = pd.DataFrame(data_rows, columns=["Order ID", "Customer Name", "Customer Address", "Pin Code", 
                                           "City", "Mobile Number", "SKU", "Price", "Quantity", 
                                           "Shipping Charges", "Total Quantity", "Total Price"])

    return df

def get_download_link(file_path, text):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('utf-8')
    href = f'<a href="data:file/xlsx;base64,{b64}" download="{file_path}">{text}</a>'
    return href

def main():
    st.title("Upload Your Orders PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())

        df = extract_data_from_pdf("temp.pdf")
        
        excel_path = "shipping_order_data.xlsx"
        df.to_excel(excel_path, index=False)
        
        st.success("Data processed successfully!")
        st.markdown(get_download_link('shipping_order_data.xlsx',
                    'Download Excel file'), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
