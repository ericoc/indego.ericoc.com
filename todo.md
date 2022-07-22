
# Thoughts/TODO

### Database before API

- Make a dbc function

- The index hits the API on every GET right now so it's crazy slow pulling 179(+) stations each time.
- I created `/new` which is pulling all stations from the database, but I have to make search work with it.
- I should stop using my `indego-py-lib` and just get all the data from PostgreSQL since I am pulling it every ten (10) minutes anyways.

- Example search for name/address (`name` / `addressStreet`)that should work in code eventually/hopefully?

```
SELECT
    station->'properties'->'id' "kioskId",
    station->'properties' "properties"
FROM
    indego,
    jsonb_array_elements(indego.data->'features') station
WHERE
    ((station->'properties'->>'name' ILIKE '%broad%'
    OR
    station->'properties'->>'addressStreet' ILIKE '%broad%')
    AND
    added = (SELECT MAX(added) from indego WHERE data IS NOT NULL))
ORDER BY
    indego.added DESC;
```

- Similarly, for zip/postal codes (`addressZipCode`):

```
SELECT
    station->'properties'->'id' "kioskId",
    station->'properties' "properties"
FROM
    indego,
    jsonb_array_elements(indego.data->'features') station
WHERE
    station->'properties'->>'addressZipCode' = '19103'
        AND
    added = (SELECT MAX(added) from indego WHERE data IS NOT NULL)
ORDER BY
    indego.added DESC;
```

- And, finally station ID (`kioskId`):

```
SELECT
    station->'properties'->'id' "kioskId",
    station->'properties' "properties"
FROM
    indego,
    jsonb_array_elements(indego.data->'features') station
WHERE
    station->'properties'->'id' = '3100'
        AND
    added = (SELECT MAX(added) from indego WHERE data IS NOT NULL)
ORDER BY
    indego.added DESC;
```
