import os, re
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF


class BlogToPDF:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.visited_links = set()

    def get_latest_blog_url(self):
        """Finds the latest blog link from the primary section of the base URL."""
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            primary_section = soup.find('section', id='primary')
            if not primary_section:
                print("Primary section not found.")
                return None

            latest_blog_link = primary_section.find('a', href=True)
            if latest_blog_link:
                latest_blog_url = latest_blog_link['href']
                if latest_blog_url.startswith('/'):
                    # Remove '/shuiqiangushi' from base URL if present
                    return f"{self.base_url.split('/shuiqiangushi')[0]}{latest_blog_url}"
                return latest_blog_url

            print("Latest blog link not found.")
            return None
        except requests.RequestException as e:
            print(f"Error fetching the blog list page: {e}")
            return None

    def get_main_image_from_page(self, url):
        """Extracts the main image URL and next page link from a blog page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the main image from the blog page
            image_tag = soup.find('main').find('img') if soup.find('main') else None
            image_url = image_tag['src'] if image_tag and image_tag.get('src') else None

            # Extract next page link
            next_page_link = soup.find('a', string='下一页')
            next_page_url = next_page_link['href'] if next_page_link else None

            return image_url, next_page_url
        except requests.RequestException as e:
            print(f"Error fetching page {url}: {e}")
            return None, None

    def save_image_to_pdf(self, image_url, pdf, is_last_page=False, latest_blog_url=None):
        """Downloads an image and adds it to the PDF."""
        full_image_url = image_url if image_url.startswith('http') else f"{self.base_url}/{image_url.lstrip('/')}"
        try:
            response = requests.get(full_image_url, stream=True, timeout=10)
            response.raise_for_status()
            image_path = full_image_url.split("/")[-1]

            with open(image_path, 'wb') as file:
                file.write(response.content)

            pdf.add_page()
            # pdf.image(image_path, x=10, y=10, w=190)
            # self.add_page_number(pdf)  # Add page number after adding the image
            # if is_last_page and latest_blog_url:
            #     self.add_latest_blog_url(pdf, latest_blog_url)
            os.remove(image_path)
        except requests.RequestException as e:
            print(f"Error downloading image {full_image_url}: {e}")
        except Exception as e:
            print(f"Error adding image {full_image_url} to PDF: {e}")

    def add_page_number(self, pdf):
        """Adds a page number to the bottom of the current page."""
        pdf.set_y(-15)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, f'Page {pdf.page_no()}', 0, 0, 'C')

    def add_latest_blog_url(self, pdf, latest_blog_url):
        """Adds the latest blog URL to the bottom of the last page."""
        pdf.set_y(-30)
        pdf.set_font('Arial', 'I', 8)
        pdf.multi_cell(0, 10, f'Latest blog URL: {latest_blog_url}', 0, 'C')

    def scrape_and_generate_pdf(self):
        """Automates the process of finding the latest blog and generating a PDF."""
        latest_blog_url = self.get_latest_blog_url()
        if not latest_blog_url:
            print("Failed to find the latest blog.")
            return

        if not latest_blog_url.startswith('http'):
            latest_blog_url = f"{self.base_url.rstrip('/')}/{latest_blog_url.lstrip('/')}"

        pdf = FPDF()
        current_url = latest_blog_url

        while current_url and current_url not in self.visited_links:
            self.visited_links.add(current_url)
            image_url, next_page_url = self.get_main_image_from_page(current_url)
            if image_url:
                is_last_page = not next_page_url
                self.save_image_to_pdf(image_url, pdf, is_last_page, latest_blog_url)
            current_url = next_page_url

        if pdf.page_no() > 0:
            pattern = r'/(\d+)\.html'  # Matches the last number in the string
            match = re.search(pattern, latest_blog_url)
            if match:
                story_id = match.group(1)
            else:
                story_id = 'new'
            output_pdf_path = f"story_{story_id}.pdf"
            pdf.output(output_pdf_path)
            print(f"PDF saved as {output_pdf_path}")
        else:
            print("No images found to save in the PDF.")


if __name__ == "__main__":
    base_url = "https://www.gushi365.com/shuiqiangushi/"  # Blog list page

    blog_to_pdf = BlogToPDF(base_url)
    blog_to_pdf.scrape_and_generate_pdf()
