-- Create a file: /Users/robertlee/GitHubProjects/ollama-inference-app/scripts/create_all_vector_helpers.sql

-- Comprehensive helper functions for vector operations
BEGIN;

-- 1. Create a properly sized vector from an array
CREATE OR REPLACE FUNCTION create_embedding_vector(input_array float[])
RETURNS vector AS $$
DECLARE
    required_size INTEGER := 3076;
    input_size INTEGER;
    result_array float[];
BEGIN
    -- Handle NULL input
    IF input_array IS NULL THEN
        RETURN NULL;
    END IF;
    
    input_size := array_length(input_array, 1);
    
    -- Handle empty array
    IF input_size IS NULL THEN
        RETURN array_fill(0::float, ARRAY[required_size])::vector(3076);
    END IF;
    
    -- Check if the input array has exactly the required size
    IF input_size = required_size THEN
        RETURN input_array::vector(3076);
    
    -- If the input array is exactly the internal size (3072)
    ELSIF input_size = 3072 THEN
        -- Add padding to match the declared size
        result_array := input_array || array_fill(0::float, ARRAY[4]);
        RETURN result_array::vector(3076);
    
    -- If the input array is smaller, pad with zeros
    ELSIF input_size < required_size THEN
        result_array := input_array || array_fill(0::float, ARRAY[required_size - input_size]);
        RETURN result_array::vector(3076);
    
    -- If the input array is larger, truncate
    ELSE
        result_array := input_array[1:required_size];
        RETURN result_array::vector(3076);
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error creating vector: %', SQLERRM;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 2. Create a zero vector of the correct size
CREATE OR REPLACE FUNCTION create_zero_vector()
RETURNS vector AS $$
BEGIN
    RETURN array_fill(0::float, ARRAY[3076])::vector(3076);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. Create a random vector of the correct size
CREATE OR REPLACE FUNCTION create_random_vector()
RETURNS vector AS $$
DECLARE
    random_array float[];
    i INTEGER;
BEGIN
    -- Initialize empty array
    random_array := ARRAY[]::float[];
    
    -- Fill with random values
    FOR i IN 1..3076 LOOP
        random_array := random_array || random();
    END LOOP;
    
    RETURN random_array::vector(3076);
END;
$$ LANGUAGE plpgsql VOLATILE;

-- 4. Normalize a vector to unit length
CREATE OR REPLACE FUNCTION normalize_vector(input_vector vector)
RETURNS vector AS $$
DECLARE
    magnitude FLOAT;
    normalized_array FLOAT[];
    vector_array FLOAT[];
    i INTEGER;
BEGIN
    -- Handle NULL input
    IF input_vector IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Calculate magnitude (L2 norm)
    magnitude := sqrt(input_vector <#> input_vector);
    
    -- Handle zero vector
    IF magnitude = 0 THEN
        RETURN input_vector;
    END IF;
    
    -- Convert vector to array for manipulation
    vector_array := input_vector::float[];
    normalized_array := ARRAY[]::float[];
    
    -- Normalize each component
    FOR i IN 1..array_length(vector_array, 1) LOOP
        normalized_array := normalized_array || (vector_array[i] / magnitude);
    END LOOP;
    
    -- Return as properly sized vector
    RETURN create_embedding_vector(normalized_array);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 5. Combine two vectors with specified weight
CREATE OR REPLACE FUNCTION combine_vectors(vector1 vector, vector2 vector, weight FLOAT DEFAULT 0.5)
RETURNS vector AS $$
DECLARE
    array1 FLOAT[];
    array2 FLOAT[];
    result_array FLOAT[];
    i INTEGER;
    size INTEGER;
BEGIN
    -- Handle NULL inputs
    IF vector1 IS NULL AND vector2 IS NULL THEN
        RETURN NULL;
    ELSIF vector1 IS NULL THEN
        RETURN vector2;
    ELSIF vector2 IS NULL THEN
        RETURN vector1;
    END IF;
    
    -- Convert vectors to arrays
    array1 := vector1::float[];
    array2 := vector2::float[];
    
    -- Get sizes
    size := LEAST(array_length(array1, 1), array_length(array2, 1));
    result_array := ARRAY[]::float[];
    
    -- Combine with weighting
    FOR i IN 1..size LOOP
        result_array := result_array || (array1[i] * (1 - weight) + array2[i] * weight);
    END LOOP;
    
    -- Return as properly sized vector
    RETURN create_embedding_vector(result_array);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. Get vector magnitude (L2 norm)
CREATE OR REPLACE FUNCTION get_vector_magnitude(input_vector vector)
RETURNS FLOAT AS $$
BEGIN
    -- Handle NULL input
    IF input_vector IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Calculate and return magnitude
    RETURN sqrt(input_vector <#> input_vector);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 7. Check vector dimensions
CREATE OR REPLACE FUNCTION vector_dimension_check(input_vector vector, expected_dim INTEGER)
RETURNS BOOLEAN AS $$
BEGIN
    -- Handle NULL input
    IF input_vector IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check dimension
    RETURN vector_dims(input_vector) = expected_dim;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 8. Vector similarity helper (with null handling)
CREATE OR REPLACE FUNCTION vector_similarity(vector1 vector, vector2 vector)
RETURNS FLOAT AS $$
BEGIN
    -- Handle NULL inputs
    IF vector1 IS NULL OR vector2 IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Calculate cosine distance
    RETURN vector1 <-> vector2;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 9. Vector diagnostic function
CREATE OR REPLACE FUNCTION diagnose_vector(input_vector vector)
RETURNS TABLE (
    is_null BOOLEAN,
    dimension INTEGER,
    magnitude FLOAT,
    has_nan BOOLEAN,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    zero_count INTEGER
) AS $$
DECLARE
    vec_array FLOAT[];
    nan_count INTEGER := 0;
    zeros INTEGER := 0;
    min_val FLOAT := NULL;
    max_val FLOAT := NULL;
    sum_val FLOAT := 0;
    i INTEGER;
BEGIN
    -- Check if NULL
    is_null := input_vector IS NULL;
    
    IF is_null THEN
        dimension := NULL;
        magnitude := NULL;
        has_nan := NULL;
        min_value := NULL;
        max_value := NULL;
        avg_value := NULL;
        zero_count := NULL;
        RETURN NEXT;
        RETURN;
    END IF;
    
    -- Get dimension
    dimension := vector_dims(input_vector);
    
    -- Calculate magnitude
    magnitude := get_vector_magnitude(input_vector);
    
    -- Convert to array for analysis
    vec_array := input_vector::float[];
    
    -- Analyze values
    FOR i IN 1..array_length(vec_array, 1) LOOP
        -- Check for NaN
        IF vec_array[i] != vec_array[i] THEN  -- NaN check
            nan_count := nan_count + 1;
        ELSIF vec_array[i] = 0 THEN
            zeros := zeros + 1;
        END IF;
        
        -- Track min and max
        IF vec_array[i] = vec_array[i] THEN  -- Skip NaN
            IF min_val IS NULL OR vec_array[i] < min_val THEN
                min_val := vec_array[i];
            END IF;
            
            IF max_val IS NULL OR vec_array[i] > max_val THEN
                max_val := vec_array[i];
            END IF;
            
            sum_val := sum_val + vec_array[i];
        END IF;
    END LOOP;
    
    -- Set results
    has_nan := nan_count > 0;
    min_value := min_val;
    max_value := max_val;
    avg_value := sum_val / (array_length(vec_array, 1) - nan_count);
    zero_count := zeros;
    
    RETURN NEXT;
    RETURN;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Test the functions
DO $$
DECLARE
    v1 vector;
    v2 vector;
    v3 vector;
    v4 vector;
    test_array float[];
    diag record;
BEGIN
    -- Test zero vector
    v1 := create_zero_vector();
    RAISE NOTICE 'Zero vector created with % elements', vector_dims(v1);
    
    -- Test random vector
    v2 := create_random_vector();
    RAISE NOTICE 'Random vector created with % elements', vector_dims(v2);
    
    -- Test creating from array
    test_array := ARRAY[0.1, 0.2, 0.3, 0.4, 0.5];
    v3 := create_embedding_vector(test_array);
    RAISE NOTICE 'Vector from small array created with % elements', vector_dims(v3);
    
    -- Test normalization
    v4 := normalize_vector(v2);
    RAISE NOTICE 'Normalized vector magnitude: %', get_vector_magnitude(v4);
    
    -- Test combination
    v4 := combine_vectors(v1, v2, 0.3);
    RAISE NOTICE 'Combined vector created with % elements', vector_dims(v4);
    
    -- Test similarity
    RAISE NOTICE 'Similarity between vectors: %', vector_similarity(v3, v2);
    
    -- Test dimension check
    RAISE NOTICE 'Vector dimension check (should be true): %', 
        vector_dimension_check(v3, 3076);
    
    -- Test diagnostics
    SELECT * INTO diag FROM diagnose_vector(v2);
    RAISE NOTICE 'Vector diagnosis: dimension=%, magnitude=%, min=%, max=%, avg=%, zeros=%',
        diag.dimension, diag.magnitude, diag.min_value, diag.max_value, 
        diag.avg_value, diag.zero_count;
END $$;

-- Add usage documentation
COMMENT ON FUNCTION create_embedding_vector(float[]) IS 
'Creates a vector(3076) from an input array, padding or truncating as needed to ensure 3072 internal dimensions';

COMMENT ON FUNCTION create_zero_vector() IS 
'Creates a zero-filled vector(3076) with 3072 internal dimensions';

COMMENT ON FUNCTION create_random_vector() IS 
'Creates a random vector(3076) with 3072 internal dimensions';

COMMENT ON FUNCTION normalize_vector(vector) IS 
'Normalizes a vector to unit length (L2 norm = 1)';

COMMENT ON FUNCTION combine_vectors(vector, vector, float) IS 
'Combines two vectors with the specified weight (default 0.5) for the second vector';

COMMENT ON FUNCTION get_vector_magnitude(vector) IS 
'Returns the L2 norm (magnitude) of a vector';

COMMENT ON FUNCTION vector_dimension_check(vector, integer) IS 
'Checks if a vector has the expected dimension, returns boolean';

COMMENT ON FUNCTION vector_similarity(vector, vector) IS 
'Returns the cosine similarity between two vectors with proper NULL handling';

COMMENT ON FUNCTION diagnose_vector(vector) IS 
'Returns diagnostic information about a vector (dimension, magnitude, value stats)';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '====================================================================';
    RAISE NOTICE 'Complete vector helper function suite created successfully:';
    RAISE NOTICE '';
    RAISE NOTICE '1. Basic Operations:';
    RAISE NOTICE '- create_embedding_vector(float[]): Convert array to proper vector';
    RAISE NOTICE '- create_zero_vector(): Create zero-filled vector';
    RAISE NOTICE '- create_random_vector(): Create random vector';
    RAISE NOTICE '';
    RAISE NOTICE '2. Vector Manipulation:';
    RAISE NOTICE '- normalize_vector(vector): Normalize to unit length';
    RAISE NOTICE '- combine_vectors(vector, vector, float): Weighted combination';
    RAISE NOTICE '';
    RAISE NOTICE '3. Analysis & Utilities:';
    RAISE NOTICE '- get_vector_magnitude(vector): Get L2 norm';
    RAISE NOTICE '- vector_dimension_check(vector, int): Validate dimensions';
    RAISE NOTICE '- vector_similarity(vector, vector): Safe similarity calculation';
    RAISE NOTICE '- diagnose_vector(vector): Comprehensive vector analysis';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage example:';
    RAISE NOTICE 'UPDATE code_files SET embedding = create_embedding_vector(ARRAY[0.1, 0.2, ...])';
    RAISE NOTICE 'WHERE id = 1;';
    RAISE NOTICE '====================================================================';
END $$;

COMMIT;