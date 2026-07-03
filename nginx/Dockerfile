FROM nginx:alpine
COPY conf/default.conf.template /etc/nginx/templates/default.conf.template
COPY conf/rate-limit.conf /etc/nginx/conf.d/rate-limit.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
