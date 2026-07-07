# Autenticação

## Cadastro

Em **/signup**, informe nome, e-mail e senha (mínimo 8 caracteres). Se o
projeto Supabase exigir confirmação por e-mail (padrão), você verá uma
mensagem pedindo para checar a caixa de entrada antes de conseguir entrar.

## Login

Em **/login**, entre com e-mail e senha, ou use os botões **Google**/**GitHub**
(se habilitados no projeto Supabase — ver [Configuração](../configuration.md)).
No primeiro login, seu perfil, preferências padrão e quadro Kanban inicial são
criados automaticamente.

## Esqueci minha senha

Em **/forgot-password**, informe o e-mail cadastrado; um link de redefinição é
enviado pelo Supabase Auth. Por segurança, a mensagem de confirmação é sempre
a mesma, exista ou não aquele e-mail na base.

## Sessão

A sessão fica em cookies `httpOnly` (não acessíveis via JavaScript), com
duração de 1 hora para o token de acesso e 30 dias para o de atualização.
Clique em **Sair** no menu do usuário (canto superior direito) para encerrar a
sessão em qualquer dispositivo.
