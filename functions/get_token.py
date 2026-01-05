from integration_utils.bitrix24.models import BitrixUserToken


def get_token():
    try:
        # токен какого-нибудь тех аккаунта
        token = BitrixUserToken.objects.get(user__bitrix_id=1)
    except BitrixUserToken.DoesNotExist:
        token = BitrixUserToken.objects.filter(is_active=True, user__user_is_active=True, user__is_admin=True).last()
    return token
