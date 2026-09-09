"""
Django绠＄悊鍛戒护 - 鍒涘缓鏁版嵁搴撴€ц兘浼樺寲绱㈠紩
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '鍒涘缓鏁版嵁搴撴€ц兘浼樺寲绱㈠紩'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='寮哄埗閲嶆柊鍒涘缓宸插瓨鍦ㄧ殑绱㈠紩',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # 瀹氫箟瑕佸垱寤虹殑绱㈠紩
        indexes = [
            {
                'name': 'idx_cmgdata_cmg_timestamp',
                'table': 'data_management_cmgdata',
                'columns': '(cmg_id, timestamp)',
                'description': 'PHM鏁版嵁澶嶅悎绱㈠紩锛圕MG ID + 鏃堕棿鎴筹級'
            },
            {
                'name': 'idx_cmgdata_timestamp',
                'table': 'data_management_cmgdata',
                'columns': '(timestamp)',
                'description': 'PHM鏁版嵁鏃堕棿鎴崇储寮?
            },
            {
                'name': 'idx_cmg_cmg_id',
                'table': 'data_management_cmg',
                'columns': '(cmg_id)',
                'description': 'PHM鏍囪瘑绗︾储寮?,
                'unique': True
            },
        ]
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    # 妫€鏌ョ储寮曟槸鍚﹀凡瀛樺湪
                    if not force:
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM information_schema.statistics 
                            WHERE table_schema = DATABASE() 
                            AND table_name = %s 
                            AND index_name = %s
                        """, [index['table'], index['name']])
                        
                        if cursor.fetchone()[0] > 0:
                            self.stdout.write(
                                self.style.WARNING(f"绱㈠紩 {index['name']} 宸插瓨鍦紝璺宠繃")
                            )
                            continue
                    else:
                        # 寮哄埗妯″紡锛氬厛鍒犻櫎宸插瓨鍦ㄧ殑绱㈠紩
                        try:
                            cursor.execute(f"DROP INDEX {index['name']} ON {index['table']}")
                            self.stdout.write(f"鍒犻櫎宸插瓨鍦ㄧ殑绱㈠紩: {index['name']}")
                        except:
                            pass  # 绱㈠紩涓嶅瓨鍦ㄦ椂浼氭姤閿欙紝蹇界暐
                    
                    # 鍒涘缓绱㈠紩
                    unique_keyword = 'UNIQUE' if index.get('unique') else ''
                    sql = f"CREATE {unique_keyword} INDEX {index['name']} ON {index['table']} {index['columns']}"
                    
                    self.stdout.write(f"姝ｅ湪鍒涘缓绱㈠紩: {index['description']}")
                    self.stdout.write(f"SQL: {sql}")
                    
                    cursor.execute(sql)
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"鉁?鎴愬姛鍒涘缓绱㈠紩: {index['name']}")
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"鉁?鍒涘缓绱㈠紩 {index['name']} 澶辫触: {str(e)}")
                    )
        
        # 鏄剧ず绱㈠紩浣跨敤寤鸿
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("绱㈠紩鍒涘缓瀹屾垚锛?))
        self.stdout.write("\n寤鸿:")
        self.stdout.write("1. 瀹氭湡鐩戞帶鎱㈡煡璇㈡棩蹇?)
        self.stdout.write("2. 鏍规嵁瀹為檯鏌ヨ妯″紡璋冩暣绱㈠紩")
        self.stdout.write("3. 瀹氭湡鏇存柊绱㈠紩缁熻淇℃伅")
        self.stdout.write("\n浣跨敤浠ヤ笅SQL妫€鏌ョ储寮曚娇鐢ㄦ儏鍐?")
        self.stdout.write("SHOW INDEX FROM data_management_cmgdata;")
        self.stdout.write("EXPLAIN SELECT * FROM data_management_cmgdata WHERE cmg_id='PHM_001' ORDER BY timestamp;")

