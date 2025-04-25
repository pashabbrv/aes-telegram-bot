from dotenv import load_dotenv
import os

load_dotenv()
managers_bachelor_list = list(map(int, os.getenv('MANAGERS_BACHELOR').split(',')))
managers_magistracy_list = list(map(int, os.getenv('MANAGERS_MAGISTRACY').split(',')))

bachelor = [
    'Промышленная электроника',
]
magistracy = [
    'Силовая микроэлектроника', 
    'Перспективные силовые преобразователи', 
    'Разработка электронных приборов и систем инерциальной навигации', 
    'Системы и технологии радиомониторинга', 
    'Автоматизация и дигитализация технологических процессов', 
    'Промышленные лазеры', 
    'Системы автоматизированного проектирования микроэлектроники', 
    'Управление проектами внедрения цифровых двойников промышленных систем', 
    'Конструирование и технологии производства элементов и устройств радиоэлектроники', 
    'Системы и технологии технического зрения',
]

managers_bachelor = dict(zip(bachelor, managers_bachelor_list))
managers_magistracy = dict(zip(magistracy, managers_magistracy_list))

# Менеджеры програм
managers = {**managers_bachelor, **managers_magistracy}
# Дирекция
management = list(map(int, os.getenv('MANAGEMENT').split(',')))
