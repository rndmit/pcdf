import json
from pydantic import ConfigDict
from pcdf.lib import datamodel


class Datamodel(datamodel.Base):
    model_config = ConfigDict()

    runtime: datamodel.Runtime
    network: datamodel.Networking
    envs: list[datamodel.EnvVar] = []


if __name__ == "__main__":
    schema = Datamodel.model_json_schema()
    with open("values.schema.json", "w") as output:
        json.dump(schema, output)
