from xmlrpc import client


server_url = 'http://localhost:8102'
db_name = 'demo'
username = 'admin'
password = 'admin'
common = client.ServerProxy('%s/xmlrpc/2/common' % server_url)
user_id = common.authenticate(db_name, username, password, {})
version_info = common.version()
if user_id:
    print("Success: User id is", user_id, 'version_info', version_info)
else:
    print("Failed: wrong credentials")

models = client.ServerProxy('%s/xmlrpc/2/object' % server_url)
if user_id:

   
 # create new books
    create_data = [
 {'name': 'Book 1', 'date_release':
 '2019-01-26'},
 {'name': 'Book 3', 'date_release':
 '2019-02-12'},
 {'name': 'Book 3', 'date_release':
 '2019-05-08'},
 {'name': 'Book 7', 'date_release':
 '2019-05-14'}
 ]
    books_ids = models.execute_kw(db_name, user_id,
 password,
 'library.book', 'create',
 [create_data])
    print("Books created:", books_ids)
 # Write in existing book record

    book_to_write = books_ids[1] # We will use ids of
 # recently created books
    write_data = {'name': 'Books 2'}
    written = models.execute_kw(db_name, user_id,
 password,
 'library.book', 'write',
 [book_to_write, write_data])
    print("Books written:", written)

    search_domain = []
    # Delete the book record
    books_to_delete = models.execute_kw(db_name, user_id, password, 
        'library.book', 'search', [search_domain], {'limit': 20})[5:] # We will use ids
 # of recently created books
    deleted = models.execute_kw(db_name, user_id,
 password,
 'library.book', 'unlink',
 [books_to_delete])
    print('Books unlinked:', deleted)



    books_ids = models.execute_kw(db_name, user_id, password, 
        'library.book', 'search', [search_domain], {'limit': 20})
    print('Books ids found:', books_ids)
    books_data = models.execute_kw(db_name, user_id,
        password,
        'library.book', 'read',
        [books_ids, ['name', 'date_release']])
    print("Books data:", *books_data, sep='\n')
else:
    print('Wrong credentials')