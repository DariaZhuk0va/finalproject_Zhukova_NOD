import functools
from valutatrade_hub.logging_config import *

def log_action_decorator(operation_name, verbose=False):
    """
    Декоратор для логирования
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if operation_name not in LOG_CONFIG['LOG_ACTIONS']:
                return func(*args, **kwargs)
            
            log_data = {}
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Проверяем, что результат - словарь
                if not isinstance(result, dict):
                    log_data['result'] = 'OK'
                    log_action(operation_name, **log_data)
                    return result
                
                log_data['result'] = 'OK' if result.get('success') else 'ERROR'
                
                # Извлекаем данные из result['data']
                if 'data' in result:
                    data = result['data']
                    
                    if 'username' in data:
                        log_data['user'] = data['username']
                    
                    if operation_name in ['BUY', 'SELL']:
                        # Важно: currency_code а не currency
                        log_data['currency_code'] = data.get('currency', 'unknown')
                        log_data['amount'] = data.get('amount', 0)
                        log_data['rate'] = data.get('rate', 0.0)
                        log_data['base'] = data.get('base', 'USD')
                    
                    # verbose режим
                    if verbose:
                        if 'wallet_before' in data:
                            log_data['wallet_before'] = str(data['wallet_before'])
                        if 'wallet_after' in data:
                            log_data['wallet_after'] = str(data['wallet_after'])
                
                # Если нет username в data, пытаемся найти в session_data
                elif 'user' not in log_data and operation_name in ['BUY', 'SELL', 'LOGIN']:
                    if args and isinstance(args[0], dict) and 'username' in args[0]:
                        log_data['user'] = args[0].get('username', 'unknown')
                
                # Логируем действие
                log_action(operation_name, **log_data)
                return result
                
            except Exception as e:
                # Ошибка
                log_data['result'] = 'ERROR'
                log_data['error_type'] = type(e).__name__
                log_data['error_message'] = str(e)
                
                # Пытаемся извлечь username для ошибок
                if operation_name in ['REGISTER', 'LOGIN'] and args and len(args) > 0:
                    # Для регистрации и входа username в первом аргументе
                    if isinstance(args[0], str):
                        log_data['user'] = args[0]
                
                # Базовые данные даже при ошибке
                if operation_name in ['BUY', 'SELL'] and len(args) > 1:
                    log_data['currency_code'] = str(args[1]).upper() if args[1] else 'unknown'
                    if len(args) > 2:
                        try:
                            log_data['amount'] = float(args[2])
                        except:
                            log_data['amount'] = args[2]
                    log_data['rate'] = 0.0
                    log_data['base'] = 'USD'
                
                log_error(operation_name, **log_data)
                raise  
        
        return wrapper
    return decorator


def log_buy(verbose=False):
    """Декоратор для покупки"""
    return log_action_decorator('BUY', verbose)

def log_sell(verbose=False):
    """Декоратор для продажи"""
    return log_action_decorator('SELL', verbose)

def log_register(verbose=False):
    """Декоратор для регистрации"""
    return log_action_decorator('REGISTER', verbose)

def log_login(verbose=False):
    """Декоратор для входа"""
    return log_action_decorator('LOGIN', verbose)
