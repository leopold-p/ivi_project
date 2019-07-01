# Тестовые сценарии, реализованные в автотесте:

## Некорректная попытка авторизации
	запрашиваем characters с корректным username и некорректным password
## Получение коллекции
	запрашиваем characters с корректными username:password
	сохраняем полученную коллекцию для дальнейших тестов
## Валидация коллекции
	проверяем, что у каждого персонажа имеются все поля, указанные в документации
## Получение одного персонажа
	запрашиваем случайно выбранного персонажа из сохраненной коллекции
	получаем данные, совпадающие с имеющимися данными
## Добавление нового песонажа
	добавляем нового персонажа
	получаем его данные
## Добавление дубликата персонажа
	добавляем персонажа с существующим в коллекции именем
	получаем ответ, что имя занято
## Добавление персонажа с некорректно составленными данными
	последовательно пробуем отправить json без каждого поля
	каждый раз получаем ожидаемый ответ 500
## Изменение данных персонажа
	изменяем данные персонажа
	запрашиваем данные измененного песонажа
	убеждаемя что полученные данные соответствуют измененным
## Изменение данных персонажа на некорректные
	последовательно пробуем отправить json без каждого поля
	каждый раз получаем ожидаемый ответ 500
## Удаление персонажа
	удаляем персонажа
	получаем ожидаемый результат
	пробуем запросить удаленного персонажа
	получаем ответ что его нет
## Удаление несуществующего персонажа
	удаляем персонажа
	получаем ожидаемый результат, что персонаж не найден
## Сброс коллекции
	добавляем нового персонажа и берем из предыдущего теста имя удаленного персонажа
	отправляем запрос на сброс коллекции
	проверяем что добавленный персонаж теперь удален, а удаленный - восстановлен
## Добавление персонажа сверх лимита
	вычисляем N - количество персонажей в коллекции
	успешно добавляем 500-N персонажей
	добавляем ещё одного
	получаем ответ, что коллекция заполнена
	пробуем запросить последнего добавленного персонажа на случай, если он все равно добавился
