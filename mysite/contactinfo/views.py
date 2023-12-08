from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import ContactInfoForm
from .models import ContactInfo
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import requests
import re
from xml.etree.ElementTree import ElementTree, Element, SubElement, tostring
from xml.dom import minidom

def create_sitemap(domain_url):
    # Function to fetch the HTML content of a given URL
    def fetch_html(url):
        response = requests.get(url)
        return response.text

    # Function to extract links from HTML content
    def extract_links(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        return [a.get('href') for a in soup.find_all('a', href=True)]

    # Function to create a sitemap XML
    def create_xml(links):
        urlset = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')

        for link in links:
            url_element = SubElement(urlset, 'url')
            loc_element = SubElement(url_element, 'loc')
            loc_element.text = link

        return minidom.parseString(tostring(urlset)).toprettyxml(indent="  ")

    # Normalize the domain URL
    domain_url = urlparse(domain_url)._replace(path='', query='', fragment='').geturl()

    # Fetch HTML content of the domain URL 
    html_content = fetch_html(domain_url)

    # Extract links from the HTML content
    links = extract_links(html_content)

    # Create sitemap XML
    sitemap_xml = create_xml(links)

    # Save the sitemap to the media directory
    media_root = settings.MEDIA_ROOT
    with open(f'{media_root}/sitemap.xml', 'w') as file:
        file.write(sitemap_xml)

    print("Sitemap generated successfully!")

def extract_contact_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract email addresses using a simple regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, soup.get_text())

    # Extract phone numbers using a simple regex pattern
    phone_pattern = r'\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    phones = re.findall(phone_pattern, soup.get_text())

    return emails, phones

def process_sitemap(sitemap_path):
    tree = ElementTree()
    tree.parse(sitemap_path)
    root = tree.getroot()

    for url_element in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc_element = url_element.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        url = loc_element.text

        # Extract contact information only from URLs containing specific keywords
        if 'contact' in url.lower():
            emails, phones = extract_contact_info(url)

            if emails or phones:
                print(f"Contact information found at {url}")
                if emails:
                    print(f"Emails: {emails}")
                if phones:
                    print(f"Phone numbers: {phones}")
                print()

def upload_url(request):
    if request.method == 'POST':
        form = ContactInfoForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            emails, phones = extract_contact_info(url)

            # Save the contact information to the database
            contact_info = ContactInfo.objects.create(
                url=url,
                emails=', '.join(emails),
                phones=', '.join(phones),
            )
            contact_info.save()

            # Create and save the sitemap.xml file
            create_sitemap(url)
            all_contacts = ContactInfo.objects.all()
            # Modify this part to render a template with the contact_info
            return render(request, 'url_upload.html', {'contact_info': contact_info, 'all_contacts':all_contacts})

    else:
        form = ContactInfoForm()
        all_contacts = ContactInfo.objects.all()

    context = {'form': form, 'all_contacts': all_contacts}

    return render(request, 'url_upload.html', context)



# def edit(request,id):
#     object=ContactInfo.objects.get(id=id)
#     return render(request,'edit.html',{'object':object})

# def delete(request,id):
#     ContactInfo.objects.filter(id=id).delete()

#     return render('url_upload.html')

def edit(request, id):
    # Retrieve the ContactInfo object based on the id
    contact_info = ContactInfo.objects.get(id=id)

    if request.method == 'POST':
        # Update the contact_info object based on the form submission
        form = ContactInfoForm(request.POST, instance=contact_info)
        if form.is_valid():
            form.save()
            return redirect('show_all_contacts')  # Redirect to the URL upload page after successful edit
    else:
        # Provide the ContactInfo object to pre-fill the form fields
        form = ContactInfoForm(instance=contact_info)

    # Fetch all contact information for display in the data table
    all_contact_info = ContactInfo.objects.all()

    return render(request, 'edit.html', {'form': form, 'contact_info': contact_info, 'all_contact_info': all_contact_info})

def delete(request, id):
    # Fetch the contact_info object
    contact_info = ContactInfo.objects.get(id=id)

    # Delete the contact_info object
    contact_info.delete()

    # Redirect to the page that shows all contacts
    return redirect('show_all_contacts') 


def show_all_contacts(request):
    # Fetch all contact information from the database
    all_contacts = ContactInfo.objects.all()

    # Render the template with the fetched data
    return redirect('upload_url')


def delete_urlcontents(request):
    # Get the list of item IDs to delete from the request
    item_ids = request.POST.getlist('ids[]')

    # Perform the delete operation
    try:
        ContactInfo.objects.filter(id__in=item_ids).delete()
        response_data = {'success': True, 'message': 'Deleted successfully.'}
    except Exception as e:
        response_data = {'success': False, 'message': str(e)}

    return JsonResponse(response_data)