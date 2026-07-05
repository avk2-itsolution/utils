from utils.bitrix_utils.bitrix_objects.main.bitrix_object_manager import BitrixObjectManager
from utils.bitrix_utils.bitrix_objects.main.response_list import ResponseList


class LeadObjectManager(BitrixObjectManager):
    """
    демки
    from utils.bitrix_utils.bitrix_objects.crm.lead_object_manager import LeadObjectManager
    # получаем всех лидов в работе у юзера id=1
    qq = LeadObjectManager(but=evg_but).list_with_filter({"ASSIGNED_BY_ID":1, 'STATUS_SEMANTIC_ID': 'P'})
    """

    object_path = 'utils.bitrix_utils.bitrix_objects.crm.lead_object.LeadObject'

    def get_all(self):
        leads = self.but.call_list_method('crm.lead.list')
        return ResponseList(leads)

    def api_list(self, filters={}, select=['ID']):
        #TODO  ХЗ есть ли толк от такого шортката??
        return ResponseList(self.but.call_list_method('crm.lead.list', {"FILTER": filters, "SELECT": select}))

    def list_with_filter(self, filter):
        # Получить список с фильтами
        # TODO улучшить как кверисеты джанго? или лучше make_filter сделать? или забить?
        # from utils.bitrix_utils.bitrix_objects.crm.lead_object_manager import LeadObjectManager
        # LeadObjectManager(but=evg_but).list_with_filter({"ASSIGNED_BY_ID":1})
        #
        result = self.but.call_list_method('crm.lead.list', {"FILTER": filter, "SELECT": ["ID"]})
        ids_list = [int(x['ID']) for x in result]
        return self.from_ids_list(ids_list)

    def id_list_by_responsible(self, responsible_id:int):
        # Возращает список id определенного ответсвенного
        # Может использоваться для замены отвественных при замещении, чтобы потом вернуть по id
        #from main_placement.classes.company_object import CompanyObject
        #return [CompanyObject(x['ID']) for x in self.but.call_list_method('crm.company.list', {"FILTER": {"ASSIGNED_BY_ID": responsible_id}, "SELECT": ["ID"]})]
        return [int(x['ID']) for x in self.but.call_list_method('crm.company.list', {"FILTER": {"ASSIGNED_BY_ID": responsible_id}, "SELECT": ["ID"]})]



