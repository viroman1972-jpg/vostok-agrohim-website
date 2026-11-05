<?php
// Плохой пример для самопроверки: согласие не проверяется, нет ловушки и частоты, пароль в файле, телефоны не подставлены
const PHONE_MOBILE = '%%PHONE_MOBILE%%';
$cfg = ['smtp_pass' => 'secret123'];
mail('vostokxim@mail.ru', 'Заявка', $_POST['name'] ?? '');
echo 'ok';
