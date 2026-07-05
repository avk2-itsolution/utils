from utils.bitrix_utils.bitrix_objects.main.bitrix_object import BitrixObject


class LeadObject(BitrixObject):

    # 30 - Назначен ответственный
    # FIELD_STATUS_ID = ('STATUS_ID', 'STATUS_ID', BitrixObject.CONVERT_RULE_INT)
    # FIELD_ASSIGNED_BY_ID = ('ASSIGNED_BY_ID', 'ASSIGNED_BY_ID', BitrixObject.CONVERT_RULE_INT)
    #
    # def __init__(self, id, bitrix_data=None):
    #     self.id = id
    #     self.but = get_token.get_super_token()
    #     self._bitrix_data = bitrix_data
    #     self._ones_data = None
    #     self._link_contacts_ids = list()
    #     self._link_companies_ids = list()
    #     self._link_leads_ids = list()
    #     self.is_dubles_checked = False
    #     self._portals = list()
    #     self._apps_len = None
    #     self._bundle_len = None
    #
    # def __str__(self):
    #     return f"{self.id} {self.bitrix_data['TITLE']}".strip()

    @property
    def bitrix_data(self):

        if not self._bitrix_data:
            self._bitrix_data = self.but.call_api_method('crm.lead.get', {"ID": self.id})['result']

        return self._bitrix_data

    # @property
    # def link_companies(self):
    #     if not self.is_dubles_checked:
    #         self.check_crm_duplicates()
    #         self.is_dubles_checked = True
    #     from main_placement.classes.company_object import CompanyObject
    #     companies = []
    #     for c in self._link_companies_ids:
    #         companies.append(CompanyObject(c))
    #     for contact in self.link_contacts:
    #         if contact.company and str(contact.company.id) not in self._link_companies_ids:
    #             companies.append(contact.company)
    #     return companies
    #
    # @property
    # def link_contacts(self):
    #     if not self.is_dubles_checked:
    #         self.check_crm_duplicates()
    #         self.is_dubles_checked = True
    #     from main_placement.classes.contact_object import ContactObject
    #     contacts = []
    #     for c in self._link_contacts_ids:
    #         contacts.append(ContactObject(c))
    #     return contacts
    #
    # @property
    # def link_leads(self):
    #     if not self.is_dubles_checked:
    #         self.check_crm_duplicates()
    #         self.is_dubles_checked = True
    #     leads = []
    #     for lead in self._link_leads_ids:
    #         leads.append(LeadObject(lead))
    #     return leads
    #
    # def check_crm_duplicates(self):
    #     # находит сущности с теми же контактами
    #     import re
    #     phones = [phone['VALUE'] for phone in self.bitrix_data.get('PHONE', [])]
    #     emails = [phone['VALUE'] for phone in self.bitrix_data.get('EMAIL', [])]
    #     stop_contacts = ["*it-solution.ru", "it-solution.ru", "itsolution.ru@gmail.com", "b24.it-solution.ru"]
    #     filtered_emails = []
    #     for email in emails:
    #         is_stop = False
    #         for stop_contact in stop_contacts:
    #             stop_re = re.compile(
    #                 re.escape(stop_contact).replace(re.escape('*'), '.*').replace(re.escape('?'), '.'))
    #             if stop_re.match(email) is not None:
    #                 is_stop = True
    #                 break
    #         if not is_stop:
    #             filtered_emails.append(email)
    #     emails = filtered_emails
    #     self.add_links_from_dubles(self.but.call_list_method('crm.duplicate.findbycomm', {'type': 'EMAIL', 'values': emails}) if emails else {})
    #     self.add_links_from_dubles(self.but.call_list_method('crm.duplicate.findbycomm', {'type': 'PHONE', 'values': phones}) if phones else {})
    #     self.add_links_from_sites(self.sites)
    #
    # def add_links_from_dubles(self, dubles):
    #     for entity, entity_ids in dubles.items():
    #         if entity == 'LEAD':
    #             for bx_id in entity_ids:
    #                 if bx_id != self.id and bx_id not in self._link_leads_ids:
    #                     self._link_leads_ids.append(bx_id)
    #         if entity == 'CONTACT':
    #             for bx_id in entity_ids:
    #                 if bx_id not in self._link_contacts_ids:
    #                     self._link_contacts_ids.append(bx_id)
    #         if entity == 'COMPANY':
    #             for bx_id in entity_ids:
    #                 if bx_id not in self._link_companies_ids:
    #                     self._link_companies_ids.append(bx_id)
    #
    # def add_links_from_sites(self, sites):
    #     # добавляем сущности из сайтов
    #     if sites:
    #         methods = []
    #         for i in range(len(sites)):
    #             # формат filter: {'WEB': []} ищет только по первому элементу списка поэтому так
    #             methods.append(('companies' + str(i), 'crm.company.list', {'FILTER': {'WEB': [sites[i], f"http://{sites[i]}", f"https://{sites[i]}"]}}))
    #             methods.append(('contacts' + str(i), 'crm.contact.list', {'FILTER': {'WEB': [sites[i], f"http://{sites[i]}", f"https://{sites[i]}"]}}))
    #             methods.append(('leads' + str(i), 'crm.lead.list', {'FILTER': {'WEB': [sites[i], f"http://{sites[i]}", f"https://{sites[i]}"]}}))
    #         result = self.but.batch_api_call(methods)
    #         for key, value in result.successes.items():
    #             data = value['result']
    #             if data:
    #                 if 'companies' in key:
    #                     for c in data:
    #                         if c['ID'] not in self._link_companies_ids:
    #                             self._link_companies_ids.append(c['ID'])
    #                 if 'contacts' in key:
    #                     for c in data:
    #                         if c['ID'] not in self._link_contacts_ids:
    #                             self._link_contacts_ids.append(c['ID'])
    #                 if 'leads' in key:
    #                     for lead in data:
    #                         if lead['ID'] != str(self.id) and lead['ID'] not in self._link_leads_ids:
    #                             self._link_leads_ids.append(lead['ID'])
    #
    # @property
    # def url(self):
    #     from django.conf import settings
    #     return f"https://{settings.APP_SETTINGS.portal_domain}/crm/lead/details/{self.id}/"
    #
    # @property
    # def view_url(self):
    #     from django.conf import settings
    #     return f"https://{settings.APP_SETTINGS.app_domain}/main_placement/lead_view/lead_id={self.id}"
    #
    #
    # @property
    # def sites(self):
    #     res = [x['VALUE'].replace('https://', '').replace('http://', '') for x in self.bitrix_data.get('WEB', [])]
    #     return res
    #
    # @property
    # def portals(self):
    #     if not self._portals:
    #         from main_placement.classes.portal_object import PortalObject
    #         for site in self.sites:
    #             self._portals.append(PortalObject(site))
    #     return self._portals
    #
    # @property
    # def activities(self):
    #     from main_placement.classes.activity_object import ActivityObject
    #     acts = self.but.call_list_method('crm.activity.list', {
    #         'FILTER': {'OWNER_TYPE_ID': 1, 'OWNER_ID': self.id, 'COMPLETED': 'N'}}, timeout=60)
    #     return [ActivityObject(a['ID'], a) for a in acts]
    #
    # @property
    # def apps_len(self):
    #     if self._apps_len is None:
    #         result = 0
    #         for p in self.portals:
    #             result += len(p.apps)
    #         self._apps_len = result
    #         return result
    #     else:
    #         return self._apps_len
    #
    # @property
    # def bundle_len(self):
    #     if self._bundle_len is None:
    #         result = 0
    #         for p in self.portals:
    #             for b in p.bundle_apps:
    #                 if b.get('date_to') and b['date_to'] > datetime.date.today():
    #                     result += 1
    #         self._bundle_len = result
    #         return result
    #     else:
    #         return self._bundle_len