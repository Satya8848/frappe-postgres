# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals
import frappe
import unittest
from bs4 import BeautifulSoup

from frappe.utils import set_request
from frappe.website.render import render
from frappe.utils import random_string

class TestBlogPost(unittest.TestCase):
	def test_generator_view(self):
		pages = frappe.get_all('Blog Post', fields=['name', 'route'],
			filters={'published': 1, 'route': ('!=', '')}, limit =1)

		set_request(path=pages[0].route)
		response = render()

		self.assertTrue(response.status_code, 200)

		html = response.get_data().decode()
		self.assertTrue('<article class="blog-content" itemscope itemtype="http://schema.org/BlogPosting">' in html)

	def test_generator_not_found(self):
		pages = frappe.get_all('Blog Post', fields=['name', 'route'],
			filters={'published': 0}, limit =1)

		frappe.db.set_value('Blog Post', pages[0].name, 'route', 'test-route-000')

		set_request(path='test-route-000')
		response = render()

		self.assertTrue(response.status_code, 404)

	def test_category_link(self):
		# Make a temporary Blog Post (and a Blog Category)
		blog = make_test_blog()

		# Visit the blog post page
		set_request(path=blog.route)
		blog_page_response = render()
		blog_page_html = frappe.safe_decode(blog_page_response.get_data())

		# On blog post page find link to the category page
		soup = BeautifulSoup(blog_page_html, "lxml")

		category_page_link = list(soup.find_all('a', string=blog.blog_category))[0]
		category_page_url = category_page_link["href"]

		# Visit the category page (by following the link found in above stage)
		set_request(path=category_page_url)
		category_page_response = render()
		category_page_html = frappe.safe_decode(category_page_response.get_data())

		# Category page should contain the blog post title
		self.assertIn(blog.title, category_page_html)

		# Cleanup afterwords
		frappe.delete_doc("Blog Post", blog.name)
		frappe.delete_doc("Blog Category", blog.blog_category)

def make_test_blog():
	if not frappe.db.exists('Blog Category', '-test-blog-category'):
		# Set different title and name for the category
		frappe.get_doc(dict(
			doctype = 'Blog Category',
			title='Test Blog Category')).insert()
	if not frappe.db.exists('Blogger', 'test-blogger'):
		frappe.get_doc(dict(
			doctype = 'Blogger',
			short_name='test-blogger',
			full_name='Test Blogger')).insert()
	test_blog = frappe.get_doc(dict(
		doctype = 'Blog Post',
		blog_category = '-test-blog-category',
		blogger = 'test-blogger',
		title = random_string(20),
		route = random_string(20),
		content = random_string(20),
		published = 1
	)).insert()

	return test_blog

