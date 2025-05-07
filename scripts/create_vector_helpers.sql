-- Create vector helper functions for pgvector operations

-- Function to create a zero vector with the right dimensions
CREATE OR REPLACE FUNCTION create_zero_vector()
RETURNS vector AS $$
BEGIN
    -- Return a 3076-dimensional vector initialized to zeros
    -- (will be stored as 3072 dimensions internally)
    RETURN array_fill(0::float, ARRAY[3076])::vector(3076);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error creating zero vector: %', SQLERRM;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to create a random vector
CREATE OR REPLACE FUNCTION create_random_vector()
RETURNS vector AS $$
DECLARE
    result_array float[];
    i integer;
BEGIN
    -- Initialize empty array
    result_array := ARRAY[]::float[];
    
    -- Generate 3076 random values (stored as 3072 dimensions internally)
    FOR i IN 1..3076 LOOP
        result_array := result_array || random();
    END LOOP;
    
    -- Return as vector
    RETURN result_array::vector(3076);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error creating random vector: %', SQLERRM;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Function to get vector magnitude
CREATE OR REPLACE FUNCTION get_vector_magnitude(input_vector vector)
RETURNS FLOAT AS $$
DECLARE
    dot_product FLOAT;
BEGIN
    -- Handle NULL input
    IF input_vector IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Calculate dot product safely
    SELECT input_vector <#> input_vector INTO dot_product;
    
    -- Ensure non-negative (shouldn't happen with valid vectors, but just in case)
    IF dot_product < 0 THEN
        RAISE WARNING 'Negative dot product detected: %. Using absolute value.', dot_product;
        dot_product := abs(dot_product);
    END IF;
    
    -- Calculate and return magnitude
    RETURN sqrt(dot_product);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to normalize a vector
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
    
    -- Calculate magnitude (L2 norm) using our safe function
    magnitude := get_vector_magnitude(input_vector);
    
    -- Handle zero vector
    IF magnitude = 0 OR magnitude IS NULL THEN
        RETURN input_vector;
    END IF;
    
    -- Convert vector to array for manipulation
    vector_array := input_vector::float[];
    normalized_array := ARRAY[]::float[];
    
    -- Normalize each component
    FOR i IN 1..array_length(vector_array, 1) LOOP
        normalized_array := normalized_array || (vector_array[i] / magnitude);
    END LOOP;
    
    -- Return as vector
    RETURN normalized_array::vector(3076);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to create a properly dimensioned embedding vector
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

-- Function to calculate vector similarity
CREATE OR REPLACE FUNCTION vector_similarity(vector1 vector, vector2 vector)
RETURNS FLOAT AS $$
BEGIN
    -- Handle NULL inputs
    IF vector1 IS NULL OR vector2 IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Return cosine similarity (1 - cosine distance)
    -- Lower distance means higher similarity
    RETURN 1 - (vector1 <-> vector2);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Error calculating vector similarity: %', SQLERRM;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to diagnose vector issues
CREATE OR REPLACE FUNCTION diagnose_vector(input_vector vector)
RETURNS TABLE(
    dimension integer,
    declared_dimension integer,
    internal_dimension integer,
    magnitude float,
    has_nan boolean,
    has_inf boolean,
    has_zero boolean,
    min_value float,
    max_value float,
    mean_value float
) AS $$
DECLARE
    v_array float[];
    v_dim integer;
    v_declared_dim integer;
    v_mag float;
    v_has_nan boolean := false;
    v_has_inf boolean := false;
    v_has_zero boolean := false;
    v_min float := NULL;
    v_max float := NULL;
    v_sum float := 0;
    v_count integer := 0;
    i integer;
BEGIN
    -- Handle NULL input
    IF input_vector IS NULL THEN
        dimension := NULL;
        declared_dimension := NULL;
        internal_dimension := NULL;
        magnitude := NULL;
        has_nan := NULL;
        has_inf := NULL;
        has_zero := NULL;
        min_value := NULL;
        max_value := NULL;
        mean_value := NULL;
        RETURN NEXT;
        RETURN;
    END IF;
    
    -- Get vector dimensions
    v_dim := vector_dims(input_vector);
    v_declared_dim := v_dim;
    v_array := input_vector::float[];
    
    -- Calculate internal dimension
    v_declared_dim := v_dim;
    IF v_dim > 4 THEN
        v_dim := v_dim - 4; -- Account for pgvector's dimension offset
    END IF;
    
    -- Calculate magnitude
    v_mag := get_vector_magnitude(input_vector);
    
    -- Analyze vector elements
    FOR i IN 1..array_length(v_array, 1) LOOP
        -- Check for NaN
        IF v_array[i] != v_array[i] THEN -- NaN check
            v_has_nan := true;
        -- Check for Infinity
        ELSIF v_array[i] = 'Infinity'::float OR v_array[i] = '-Infinity'::float THEN
            v_has_inf := true;
        -- Check for zero
        ELSIF v_array[i] = 0 THEN
            v_has_zero := true;
        END IF;
        
        -- Update min/max/sum
        IF v_array[i] = v_array[i] AND v_array[i] != 'Infinity'::float AND v_array[i] != '-Infinity'::float THEN
            IF v_min IS NULL OR v_array[i] < v_min THEN
                v_min := v_array[i];
            END IF;
            
            IF v_max IS NULL OR v_array[i] > v_max THEN
                v_max := v_array[i];
            END IF;
            
            v_sum := v_sum + v_array[i];
            v_count := v_count + 1;
        END IF;
    END LOOP;
    
    -- Return results
    dimension := array_length(v_array, 1);
    declared_dimension := v_declared_dim;
    internal_dimension := v_dim;
    magnitude := v_mag;
    has_nan := v_has_nan;
    has_inf := v_has_inf;
    has_zero := v_has_zero;
    min_value := v_min;
    max_value := v_max;
    
    -- Calculate mean, handling empty array case
    IF v_count > 0 THEN
        mean_value := v_sum / v_count;
    ELSE
        mean_value := NULL;
    END IF;
    
    RETURN NEXT;
    RETURN;
END;
$$ LANGUAGE plpgsql;