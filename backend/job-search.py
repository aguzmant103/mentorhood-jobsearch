"""
Goal: Searches for job listings, evaluates relevance based on a CV, and applies 

@dev You need to add OPENAI_API_KEY to your environment variables.
Also you have to install PyPDF2 to read pdf files: pip install PyPDF2
"""

import csv
import os
import sys
from pathlib import Path
import logging
from typing import List, Optional
import asyncio
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from browser_use import ActionResult, Agent, Controller
from browser_use.browser.context import BrowserContext
from browser_use.browser.browser import Browser, BrowserConfig

# Validate required environment variables
load_dotenv()
required_env_vars = ["OPENAI_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set. Please add it to your environment variables.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# full screen mode
controller = Controller()

# Add at the start of the script
parser = argparse.ArgumentParser()
parser.add_argument('--cv', type=str, required=True, help='Path to CV file')
args = parser.parse_args()

# Update CV path
CV = Path(args.cv)

if not CV.exists():
	raise FileNotFoundError(f'You need to set the path to your cv file in the CV variable. CV file not found at {CV}')


class Job(BaseModel):
	title: str
	link: str
	company: str
	fit_score: float
	location: Optional[str] = None
	salary: Optional[str] = None


@controller.action('Save jobs to file - with a score how well it fits to my profile', param_model=Job)
def save_jobs(job: Job):
	with open('jobs.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		writer.writerow([job.title, job.company, job.link, job.salary, job.location])

	return 'Saved job to file'


@controller.action('Read jobs from file')
def read_jobs():
	with open('jobs.csv', 'r') as f:
		return f.read()


@controller.action('Read my cv for context to fill forms')
def read_cv():
	pdf = PdfReader(CV)
	text = ''
	for page in pdf.pages:
		text += page.extract_text() or ''
	logger.info(f'Read cv with {len(text)} characters')
	return ActionResult(extracted_content=text, include_in_memory=True)


@controller.action(
	'Upload cv to element - call this function to upload if element is not found, try with different index of the same upload element',
)
async def upload_cv(index: int, browser: BrowserContext):
	path = str(CV.absolute())
	dom_el = await browser.get_dom_element_by_index(index)

	if dom_el is None:
		return ActionResult(error=f'No element found at index {index}')

	file_upload_dom_el = dom_el.get_file_upload_element()

	if file_upload_dom_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	file_upload_el = await browser.get_locate_element(file_upload_dom_el)

	if file_upload_el is None:
		logger.info(f'No file upload element found at index {index}')
		return ActionResult(error=f'No file upload element found at index {index}')

	try:
		await file_upload_el.set_input_files(path)
		msg = f'Successfully uploaded file "{path}" to index {index}'
		logger.info(msg)
		return ActionResult(extracted_content=msg)
	except Exception as e:
		logger.debug(f'Error in set_input_files: {str(e)}')
		return ActionResult(error=f'Failed to upload file to index {index}')


browser = Browser(
	config=BrowserConfig(
		chrome_instance_path=os.getenv('BROWSER_USE_CHROME_PATH', '/usr/bin/chromium'),
		headless=True,
		disable_security=True,
		cdp_url='http://0.0.0.0:9222',  # Specify CDP URL directly
		extra_chromium_args=[
			"--no-sandbox",
			"--disable-dev-shm-usage",
			"--disable-gpu"
		]
	)
)


@controller.action('Click filter dropdown - ensure it is the correct one')
async def click_filter(browser: BrowserContext):
	elements = await browser.get_dom_elements_by_text("Locations")
	
	if not elements:
		return ActionResult(error="Locations filter not found")

	locations_filter = elements[0]  # Assume first instance is correct
	await locations_filter.click()
	return ActionResult(extracted_content="Clicked Locations filter")


@controller.action('Scroll and find filter with max attempts')
async def scroll_for_filter(browser: BrowserContext):
	MAX_SCROLL_ATTEMPTS = 3
	scroll_attempts = 0

	while scroll_attempts < MAX_SCROLL_ATTEMPTS:
		filter_element = await browser.get_dom_elements_by_text("Locations")
		if filter_element:
			break
		await browser.scroll_down(1000)
		scroll_attempts += 1
		await asyncio.sleep(1)  # Small delay between scrolls

	if scroll_attempts >= MAX_SCROLL_ATTEMPTS:
		return ActionResult(error="Failed to find Locations filter after scrolling")
	
	return ActionResult(extracted_content="Found Locations filter")


@controller.action('Verify correct page before clicking filters')
async def verify_page(browser: BrowserContext):
	page_title = await browser.get_page_title()
	if "Google Careers" not in page_title:
		return ActionResult(error="Not on Google Careers page, retrying...")
	return ActionResult(extracted_content="On correct page")


async def main():
	try:
		ground_task = (
			'You are a professional job finder. Follow these steps:\n'
			'1. Read my cv with read_cv\n'
			'2. Go to Google Careers page\n'
			'3. Verify you are on the correct page using verify_page\n'
			'4. Use scroll_for_filter to find the Locations filter\n'
			'5. Click the filter using click_filter\n'
			'6. Find solution engineers remote roles and save them to a file\n'
			'search at company:'
		)
		tasks = [
			ground_task + '\n' + 'Google',
		]
		model = ChatOpenAI(
			model='gpt-4o',
		)

		agents = []
		for task in tasks:
			agent = Agent(task=task, llm=model, controller=controller, browser=browser)
			agents.append(agent)

		await asyncio.gather(*[agent.run() for agent in agents])
	except Exception as e:
		logger.error(f"Error in main: {str(e)}")
		raise


if __name__ == "__main__":
	asyncio.run(main())