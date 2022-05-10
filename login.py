def loginscreen():
    screen = pygame.display.set_mode((640, 480))
    font = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()
    input_box1 = pygame.Rect(100, 100, 140, 32)
    input_box2 = pygame.Rect(100, 300, 140, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the user clicked on the input_box rect.
                if input_box1.collidepoint(event.pos) or input_box2.collidepoint(event.pos):
                    # Toggle the active variable.
                    active = not active
                else:
                    active = False
                # Change the current color of the input box.
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        print(text)
                        text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((30, 30, 30))
        # Render the current text.
        txt_surface = font.render(text, True, color)
        # Resize the box if the text is too long.
        width = max(200, txt_surface.get_width()+10)
        input_box1.w = width
        input_box2.w = width
        # Blit the text.
        screen.blit(txt_surface, (input_box1.x+5, input_box1.y+5))
        screen.blit(txt_surface, (input_box2.x+5, input_box2.y+5))
        # Blit the input_box rect.
        pygame.draw.rect(screen, color, input_box1, 2)
        pygame.draw.rect(screen, color, input_box2, 2)

        draw_text('Click button to Login', font, (255, 255, 255), screen, 50, 70)
 
        mx, my = pygame.mouse.get_pos()
 
        button_1 = pygame.Rect(300, 100, 200, 50)
        if button_1.collidepoint((mx, my)):
            if click:
                main_menu()
        pygame.draw.rect(screen, (255, 0, 0), button_1)

        pygame.display.flip()
        clock.tick(30)