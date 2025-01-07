import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os

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
                if latest_blog_url.startswith('/'):  # Adjust URL
                    return f"{self.base_url.split('/shuiqiangushi')[0]}{latest_blog_url}"
                return latest_blog_url

            print("Latest blog link not found.")
            return None
        except requests.RequestException as e:
            print(f"Error fetching the blog list page: {e}")
            return None

    def get_main_image_and_next_page(self, url):
        """Extracts the main image URL and next page link from a blog page."""
        try:
            full_url = url if url.startswith('http') else f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract the main image from the blog page
            image_tag = soup.find('main').find('img') if soup.find('main') else None
            image_url = image_tag['src'] if image_tag and image_tag.get('src') else None

            # Extract next page link
            next_page_link = soup.find('a', string='下一页')
            next_page_url = next_page_link['href'] if next_page_link else None
            if next_page_url and next_page_url.startswith('/'):
                next_page_url = f"{self.base_url.split('/shuiqiangushi')[0]}{next_page_url}"

            return image_url, next_page_url
        except requests.RequestException as e:
            print(f"Error fetching page {url}: {e}")
            return None, None

    def save_image_to_pdf(self, image_url, pdf):
        """Downloads an image and adds it to the PDF."""
        full_image_url = image_url if image_url.startswith('http') else f"{self.base_url}/{image_url.lstrip('/')}"
        try:
            response = requests.get(full_image_url, stream=True, timeout=10)
            response.raise_for_status()
            image_path = full_image_url.split("/")[-1]

            with open(image_path, 'wb') as file:
                file.write(response.content)

            pdf.add_page()
            pdf.image(image_path, x=10, y=10, w=190)
            os.remove(image_path)
        except requests.RequestException as e:
            print(f"Error downloading image {full_image_url}: {e}")
        except Exception as e:
            print(f"Error adding image {full_image_url} to PDF: {e}")

    def scrape_and_generate_pdf(self, output_pdf_path):
        """Automates the process of finding the latest blog and generating a PDF."""
        latest_blog_url = self.get_latest_blog_url()
        if not latest_blog_url:
            print("Failed to find the latest blog.")
            return

        pdf = FPDF()
        current_url = latest_blog_url

        while current_url and current_url not in self.visited_links:
            self.visited_links.add(current_url)
            image_url, next_page_url = self.get_main_image_and_next_page(current_url)
            if image_url:
                self.save_image_to_pdf(image_url, pdf)
            current_url = next_page_url

        if pdf.page_no() > 0:
            pdf.output(output_pdf_path)
            print(f"PDF saved as {output_pdf_path}")
        else:
            print("No images found to save in the PDF.")

# Usage
if __name__ == "__main__":
    base_url = "https://www.gushi365.com/shuiqiangushi/"  # Blog list page
    output_pdf_path = "blog_images.pdf"

    blog_to_pdf = BlogToPDF(base_url)
    blog_to_pdf.scrape_and_generate_pdf(output_pdf_path)
