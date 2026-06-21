import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera could not be opened")
else:
    print("Gesture AI Studios prototype is running")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Could not read frame")
            break

        cv2.putText(frame, "Gesture AI Studios", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.putText(frame, "Press Q to exit", (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Gesture AI Studios Prototype", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()