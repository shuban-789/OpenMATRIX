FROM dolfinx/dolfinx:v0.6.0

WORKDIR /workspace

RUN pip install rich

COPY . .

CMD ["make"]