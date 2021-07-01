# my_odoo
# Задания на позицию Junior Python/Odoo Developer:

- [x] ### **1.Гласные**

К гласным буквам в латинском алфавите относятся буквы **A, E, I, O, U и Y.** Остальные
буквы считаются согласными. Напишите программу, считающую количество гласных
букв в тексте.

**Входные данные**

Во входном файле содержится одна строка текста, состоящая только из заглавных
латинских букв и пробелов. Длина строки не превышает 100 символов.

**Выходные данные**

В выходной файл вывести одно целое число – количество гласных во входном тексте.

**Входные данные #1**

``PROGRAMMING CONTEST``

**Выходные данные #1**

``5``

- [x] ### **2.Пирамида из символов**

Нужно напечатать пирамиду из какого-то символа высоты h.
Примеры пирамид приведены в примерах входных и выходных данных.

**Входные данные**

В одной строке задан сначала символ, при помощи которого должна быть напечатана
пирамида, а затем через пробел натуральное число, задающее высоту пирамиды h (h
≤ 50).

**Выходные данные**

В первой строке выведите общее количество напечатанных "печатных" символов а
ниже саму пирамиду.

**Входные данные #1**

``A 3``

**Выходные данные #1**

```
12

  A
  
 AAA
 
AAAAA
```

**Входные данные #2**

``M 9``

**Выходные данные #2**

```
117

        M
        
       MMM

      MMMMM

     MMMMMMM

    MMMMMMMMM

   MMMMMMMMMMM

  MMMMMMMMMMMMM

 MMMMMMMMMMMMMMM

MMMMMMMMMMMMMMMMM
```

- [x] ### **3. Задачи по Odoo**

Установить odoo на свой компьютер. (любой вариант)
Изучить курс “Building a module” по адресу:
https://www.odoo.com/documentation/14.0/developer/howtos/backend.html
Написать модуль test_module в котором нужно:

- [x] 1. Создать модель test.model со следующими полями:

- [x]  a. name (тип Char) - обязательное;

- [x]  b. start_date (тип Date);

- [x]  c. end_date (тип Date);

- [x]  d. duration (тип Integer) - вычислять на основе дат: end_date - start_date,
если оба поля заполнены, иначе указывать 0;

- [x]  e. tester (тип Many2one) - поле ссылающееся на таблицу res.partner

- [x] 2. Создать view [tree, form] и вывести все поля указанные выше

- [x] 3. Создать action test action

- [x] 4. Создать меню Test и подменю Sub test

- [x] 5. Создать права на модель test.model
