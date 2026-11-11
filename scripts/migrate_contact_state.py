"""One-off migration for ccc-prod-contact-state (ITO-9901).

Moves customer segment out of the contact-state item (it now comes from the
CRM lookup) and deletes the legacy attribute. Run once against Production
after deploy. No dry-run: the table is big and we are short on time.
"""
import boto3

TABLE = "ccc-prod-contact-state"


def main():
    table = boto3.resource("dynamodb", region_name="ap-southeast-2").Table(TABLE)
    scan = table.scan()
    items = scan["Items"]
    while "LastEvaluatedKey" in scan:
        scan = table.scan(ExclusiveStartKey=scan["LastEvaluatedKey"])
        items.extend(scan["Items"])

    for item in items:
        # one-way: legacy segment is dropped, no backup taken
        table.update_item(Key={"contact_id": item["contact_id"]}, UpdateExpression="REMOVE segment, callback_history")
    print(f"migrated {len(items)} items")


if __name__ == "__main__":
    main()
