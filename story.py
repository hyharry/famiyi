import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os

class BlogToPDF:
    def __init__(self, base_url, latest_blog_url):
        self.base_url = base_url.rstrip('/')
        self.latest_blog_url = latest_blog_url.lstrip('/')
        self.visited_links = set()

    def get_latest_blog_url(self):
        """Fetches the latest blog URL from the base page."""
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            latest_blog_link = soup.find('a', href=f"/{self.latest_blog_url}")
            if latest_blog_link:
                return f"{self.base_url}/{self.latest_blog_url}"
            print("Latest blog link not found.")
            return None
        except requests.RequestException as e:
            print(f"Error fetching latest blog URL: {e}")
            return None

    def get_main_image_from_page(self, url):
        """Extracts the main image URL from a blog page and finds the next page link."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract main image
            main_section = soup.find('main')
            if not main_section:
                print(f"Main section not found on {url}.")
                return None, None

            image_tag = main_section.find('img')
            image_url = image_tag['src'] if image_tag and image_tag.get('src') else None

            # Extract next page link
            next_page_link = soup.find('a', text='下一页')
            next_page_url = f"{self.base_url}/{next_page_link['href'].lstrip('/')}" if next_page_link else None

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
        """Crawls the blog pages, extracts images, and saves them into a PDF."""
        latest_blog_url = self.get_latest_blog_url()
        if not latest_blog_url:
            print("Failed to find the latest blog.")
            return

        pdf = FPDF()
        current_url = latest_blog_url

        while current_url and current_url not in self.visited_links:
            self.visited_links.add(current_url)
            image_url, next_page_url = self.get_main_image_from_page(current_url)
            if image_url:
                self.save_image_to_pdf(image_url, pdf)
            current_url = next_page_url

        if pdf.page_no() > 0:
            pdf.output(output_pdf_path)
            print(f"PDF saved as {output_pdf_path}")
        else:
            print("No images found to save in the PDF.")

# Improved design and fixed issues:
# - Added timeout to all requests.
# - Improved error handling and logging.
# - Avoided overwriting the `main` section logic if not present.
# - Simplified redundant checks and added more meaningful messages.
# - Removed dependency on specific HTML structure assumptions where possible.

# Usage
if __name__ == "__main__":
    base_url = "https://www.gushi365.com/"  # Base blog URL
    latest_blog_url = "info/15732.html"  # Path to the latest blog
    output_pdf_path = "blog_images.pdf"

    blog_to_pdf = BlogToPDF(base_url, latest_blog_url)
    blog_to_pdf.scrape_and_generate_pdf(output_pdf_path)
