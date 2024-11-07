import time
import uuid
from datetime import datetime

import data_requests as dr
from model import AssignedOrder, OrderAudit

order_database = {}  # amazingly fast and totally inreliable database ^
order_executer_index = {}  # amazingly fast and totally inreliable index

MAGIC_CONSTANT = 8


def handle_assign_order_request(order_id: str, executer_id: str, locale: str):
    # quite a sequential execution of requests, could be improved!
    order_data = dr.get_order_data(order_id)

    zone_info = dr.get_zone_info(order_data.zone_id)

    executer_profile = dr.get_executer_profile(executer_id)

    toll_roads = dr.get_toll_roads(zone_info.display_name)

    configs = dr.get_configs()

    # all fetcing is done, finally....
    # start building actual response

    # adjust coin_coeff with configuration settings
    actual_coin_coeff = zone_info.coin_coeff
    if configs.coin_coeff_settings is not None:
        actual_coin_coeff = min(float(configs.coin_coeff_settings['maximum']), actual_coin_coeff)
    final_coin_amount = order_data.base_coin_amount * actual_coin_coeff + toll_roads.bonus_amount

    order = AssignedOrder(
        str(uuid.uuid4()),
        order_id,
        executer_id,
        actual_coin_coeff,
        toll_roads.bonus_amount,
        final_coin_amount,
        '',
        OrderAudit(datetime.now(), None)
    )

    if executer_profile.rating >= MAGIC_CONSTANT:
        order.route_information = f'Order at zone "{zone_info.display_name}"'
    else:
        order.route_information = f'Order at somewhere'

    print(f'>> New order handled! {order}')

    # persisting order!
    order_database[order_id] = order
    order_executer_index[executer_id] = order_id


def handle_acquire_order_request(executer_id: str):
    try:
        order_id = order_executer_index[executer_id]
        # race condition is possible here!
        order_data = order_database[order_id]
        order_audit = order_data.audit
        order_audit.acquire_time = datetime.now()

        print(f'>> Order acquired!Acquire time == f{order_audit.acquire_time - order_audit.assign_time}')
        return order_data
    except KeyError:
        print(f'Order for executer ID "{executer_id}" not found!')
        return None


def handle_cancel_order_request(order_id: str):
    order_data = order_database.pop(order_id)
    # race condition is possible here!
    order_executer_index.pop(order_data.executer_id)

    print(f'>> Order was cancelled!')
    return order_data


if __name__ == '__main__':
    print('> Starting first scenario! <')
    handle_assign_order_request('some-order-id', 'some-executer-id', 'en-US')

    time.sleep(1)
    handle_acquire_order_request('some-executer-id')

    print('< First scenario is over!\n\n')

    print('> Starting second scenario! <')
    # second scenario
    handle_assign_order_request('some-order-id-to-cancel', 'another-executer-id', 'en-US')

    time.sleep(1)
    handle_cancel_order_request('some-order-id-to-cancel')
    print('< Second scenario is over!\n\n')
