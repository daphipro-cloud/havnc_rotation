FROM alpine:3.19

LABEL AboutImage="Home Assistant Dashboard through VNC"

ENV LANG=en_US.UTF-8 \
	LANGUAGE=en_US.UTF-8 \
	LC_ALL=C.UTF-8 \
	TZ="UTC"

RUN apk add --no-cache \
		bash \
		ca-certificates \
		chromium \
		font-noto \
		font-noto-cjk \
		git \
		jq \
		nginx \
		nss \
		openbox \
		python3 \
		supervisor \
		tigervnc \
		tzdata \
		websockify \
		xrandr \
		xvfb \
		&& cp "/usr/share/zoneinfo/$TZ" /etc/localtime \
		&& echo "$TZ" > /etc/timezone

ARG NOVNC_VERSION=v0.5.1
RUN git clone --depth 1 --branch "$NOVNC_VERSION" https://github.com/novnc/noVNC.git /opt/novnc \
	&& apk del git tzdata

COPY index.html /opt/novnc/index.html
COPY viewport_fit.js /opt/novnc/viewport_fit.js
COPY config /config
COPY controller.py /app/controller.py
COPY nginx.conf /etc/nginx/http.d/default.conf
RUN mkdir -p /root/.config/tigervnc

ENV VNC_TITLE="Home Assistant Dashboard" \
	DISPLAY=:0

CMD ["supervisord", "-l", "/var/log/supervisord.log", "-c", "/config/supervisord.conf"]
